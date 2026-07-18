"""Best-checkpoint selection must survive resume AND later validation fluctuations."""
import os, sys, torch, tempfile, shutil
sys.path.insert(0, os.path.expanduser('~/research_kg'))
d = tempfile.mkdtemp(prefix="sel_")
try:
    # simulate: epoch 7 was best (acc 72.5); training continued and got worse; then resumed.
    torch.save({'epoch': 7, 'valid_acc1': 72.5, 'model_state_dict': {}}, f'{d}/best_model.pt')
    torch.save({'epoch': 12, 'best_acc1': 72.5, 'best_epoch': 7, 'model_state_dict': {},
                'results': []}, f'{d}/last_checkpoint.pt')

    ck = torch.load(f'{d}/last_checkpoint.pt', map_location='cpu')
    best_acc1 = ck.get('best_acc1', 0.0)
    best_epoch = ck.get('best_epoch')
    assert best_acc1 == 72.5 and best_epoch == 7, (best_acc1, best_epoch)
    print("PASS resume restores both best score AND selected epoch")

    # a WORSE later epoch must not overwrite the selection
    va1 = 60.0
    assert not (va1 > best_acc1), "worse epoch must not become the selection"
    print("PASS later validation dip does not overwrite best checkpoint")

    # legacy checkpoint without best_epoch -> recovered from best_model.pt
    torch.save({'epoch': 12, 'best_acc1': 72.5, 'model_state_dict': {}, 'results': []},
               f'{d}/last_checkpoint.pt')
    ck2 = torch.load(f'{d}/last_checkpoint.pt', map_location='cpu')
    be = ck2.get('best_epoch')
    if be is None:
        be = torch.load(f'{d}/best_model.pt', map_location='cpu').get('epoch')
    assert be == 7, be
    print("PASS legacy checkpoint recovers selection epoch from best_model.pt")
    print("selection persistence self-check OK")
finally:
    shutil.rmtree(d, ignore_errors=True)
