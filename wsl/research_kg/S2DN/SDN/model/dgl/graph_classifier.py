from .rgcn_model import RGCN
from .layers import GraphLearner, GCN
from dgl import mean_nodes
from scipy.sparse import csr_matrix
import torch.nn as nn
import torch
import dgl
from utils.rule_features import build_rule_boost, build_rule_target_score, load_rule_index
"""
File based off of dgl tutorial on RGCN
Source: https://github.com/dmlc/dgl/tree/master/examples/pytorch/rgcn
"""

# global count=0
class GraphClassifier(nn.Module):
    def __init__(self, params, relation2id):  # in_dim, h_dim, rel_emb_dim, out_dim, num_rels, num_bases):
        super().__init__()

        self.params = params
        self.relation2id = relation2id
        # self.graph_count = 0
        self.gnn = RGCN(params)  # in_dim, h_dim, h_dim, num_rels, num_bases)
        self.rel_emb = nn.Embedding(self.params.num_rels, self.params.rel_emb_dim, sparse=False)

        self.gsl = GraphLearner(params)
        self.g_learn = GCN(self.params.emb_dim, self.params.emb_dim)
        self.rule_index = {}
        # 'score' injects symbolic evidence at the final logit (one decision per example).
        # 'adjacency' is the original Structure Refining prior, measured to touch only 0.02%
        # of node pairs and to leave the output unchanged. 'both' enables each.
        self.rule_mode = getattr(self.params, 'rule_trust_mode', 'score')
        if getattr(self.params, 'use_rule_trust', False):
            self.rule_index = load_rule_index(self.params.rule_cache, self.params.rule_conf_threshold)
        # learnable trust weight, initialised to 0 so a RuleTrust run starts bit-identical to
        # baseline and must earn its reliance on the symbolic signal
        self.rule_scale = nn.Parameter(torch.zeros(1))

        if self.params.add_ht_emb:
            self.fc_layer = nn.Linear(3 * self.params.num_gcn_layers * self.params.emb_dim + self.params.rel_emb_dim + self.params.emb_dim, 1)
            # self.fc_layer = nn.Linear(3 * self.params.num_gcn_layers * self.params.emb_dim + self.params.rel_emb_dim, 1)
        else:
            self.fc_layer = nn.Linear(self.params.num_gcn_layers * self.params.emb_dim + self.params.rel_emb_dim + self.params.emb_dim, 1)
            # self.fc_layer = nn.Linear(self.params.num_gcn_layers * self.params.emb_dim + self.params.rel_emb_dim, 1)

    def batch_graph_learner(self, batch_g, rel_labels):
        graphs = []
        rule_scores = []
        use_rules = getattr(self.params, 'use_rule_trust', False)
        # getattr keeps checkpoints pickled before these attributes existed loadable
        mode = getattr(self, 'rule_mode', 'score')
        for graph, rel_label in zip(dgl.unbatch(batch_g), rel_labels.detach().cpu().tolist()):
            rule_prior = None
            if use_rules and mode in ('adjacency', 'both'):
                rule_prior = build_rule_boost(graph, rel_label, self.rule_index)

            if use_rules and mode in ('score', 'both'):
                head = (graph.ndata['id'] == 1).nonzero().squeeze(1)
                tail = (graph.ndata['id'] == 2).nonzero().squeeze(1)
                h_i = int(head[0]) if head.numel() else None
                t_i = int(tail[0]) if tail.numel() else None
                rule_scores.append(build_rule_target_score(graph, rel_label, self.rule_index, h_i, t_i))

            node_features, learned_adj = self.gsl(graph.ndata['h'], rule_prior=rule_prior)
            csr_adj = csr_matrix(learned_adj.detach().cpu().numpy())
            learned_g = dgl.add_self_loop(dgl.from_scipy(csr_adj, eweight_name='e_w'))
            learned_g.ndata['h'] = node_features.detach().cpu()
            graphs.append(learned_g)

        batched = dgl.batch(graphs).to(self.params.device)
        target_scores = torch.stack(rule_scores).unsqueeze(1) if rule_scores else None
        return batched, target_scores

    def forward(self, data):
        g, rel_labels = data
        # g.ndata['h'] = g.ndata['feat']
        
        g.ndata['h'], kl_losses = self.gnn(g)
        g_out = mean_nodes(g, 'repr')
        # dgl.save_graphs(f'graphs/fb237/graph_original.bin',g)
        ### structure learning
        learned_g, rule_target_scores = self.batch_graph_learner(g, rel_labels)
        learned_g.ndata['id'] = g.ndata['id']
        # dgl.save_graphs(f'graphs/fb237/graph_learned.bin',learned_g)
        # import ipdb;ipdb.set_trace();
        g_repre = self.g_learn(learned_g, learned_g.ndata['h'])
        
        head_ids = (g.ndata['id'] == 1).nonzero().squeeze(1)
        head_embs = g.ndata['repr'][head_ids]

        tail_ids = (g.ndata['id'] == 2).nonzero().squeeze(1)
        tail_embs = g.ndata['repr'][tail_ids]

        if self.params.add_ht_emb:
            g_rep = torch.cat([g_out.view(-1, self.params.num_gcn_layers * self.params.emb_dim),
                               head_embs.view(-1, self.params.num_gcn_layers * self.params.emb_dim),
                               tail_embs.view(-1, self.params.num_gcn_layers * self.params.emb_dim),
                               self.rel_emb(rel_labels),
                               g_repre], dim=1)
            # g_rep = torch.cat([g_out.view(-1, self.params.num_gcn_layers * self.params.emb_dim),
            #                    head_embs.view(-1, self.params.num_gcn_layers * self.params.emb_dim),
            #                    tail_embs.view(-1, self.params.num_gcn_layers * self.params.emb_dim),
            #                    self.rel_emb(rel_labels)
            #                    ], dim=1)
        else:
            g_rep = torch.cat([g_out.view(-1, self.params.num_gcn_layers * self.params.emb_dim), self.rel_emb(rel_labels), g_repre], dim=1)
            # g_rep = torch.cat([g_out.view(-1, self.params.num_gcn_layers * self.params.emb_dim), self.rel_emb(rel_labels)], dim=1)

        output = self.fc_layer(g_rep)

        # Neurosymbolic fusion: add the symbolic evidence for THIS target triple, weighted by a
        # learnable trust scalar. rule_scale starts at 0, so training begins exactly at the
        # baseline and the model must learn how much to trust the rules.
        if rule_target_scores is not None and hasattr(self, 'rule_scale'):
            output = output + self.rule_scale * rule_target_scores.to(output.device)

        if len(kl_losses) > 0:
            kl_loss = torch.mean(kl_losses)
        else:
            kl_loss = None
        return output, kl_loss
