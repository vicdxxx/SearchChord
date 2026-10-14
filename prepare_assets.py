"""Package verified saved research outputs; no inference or scorer requests."""
from pathlib import Path
import csv, json, hashlib, math, shutil, re, difflib, statistics

ROOT = Path('D:/BoyangDeng/ImageEditing')
CHORD = ROOT / 'ChordEdit'
HERE = Path(__file__).parent
DIST = HERE / 'dist'
AUDIT = ROOT / 'tmp/searchchord_website_20261012'
PAPER = ROOT / 'CVPR/SearchChord_draft_CVPR2027_format'
METRICS = ['psnr_unedit', 'mse_unedit_x1e3', 'lpips_unedit_x1e3', 'clip_whole', 'clip_edited']
SIGN = [1, -1, -1, 1, 1]
HEADER_IDS = {'PIE': {'000000000129'}, 'CropWeed': {'Cabbage_109_soil'}}
SELECTED = {
    'PIE': ['000000000039', '122000000001', '000000000010', '114000000001',
            '000000000056', '000000000019', '000000000011', '000000000120',
            '621000000002', '621000000004', '624000000002', '612000000003'],
    'CropWeed': ['Lettuce_243_soil', 'Purslane_211_soil', 'Turnip_13_soil',
                 'Lettuce_432_soil', 'Beet_753_weather', 'Weed_148_weather',
                 'Lettuce_34_weather', 'PalmerAmaranth_200_weather',
                 'Turnip_9_leaf_amount', 'Smartweed_375_leaf_amount',
                 'Carrot_477_leaf_amount', 'Lambsquarters_687_leaf_amount']
}
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    return list(csv.DictReader(p.open(newline='', encoding='utf-8-sig')))
def metrics(r):
    return {k: float(r[k]) if math.isfinite(float(r[k])) else None for k in METRICS}
def mean(rs):
    return {k: statistics.mean(float(r[k]) for r in rs if math.isfinite(float(r[k]))) for k in METRICS}
def edit_terms(source, target):
    a = source.rstrip('.').split(); b = target.rstrip('.').split()
    before=[]; after=[]
    for tag, i, j, k, l in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag != 'equal':
            before += a[i:j]; after += b[k:l]
    return {'before': ' '.join(before) or '∅', 'after': ' '.join(after) or '∅'}

def main():
    for domain, ids in SELECTED.items():
        assert len(ids) == len(set(ids))
        assert HEADER_IDS[domain].isdisjoint(ids), 'Header examples must not repeat in the gallery'
    (DIST / 'assets/images').mkdir(parents=True, exist_ok=True)
    (DIST / 'assets/data').mkdir(exist_ok=True)
    sources={}; examples=[]; tables={}; provenance=[]
    for domain in ['PIE', 'CropWeed']:
        base = CHORD / ('scaling_full_v3' if domain == 'PIE' else 'cropweed_experiments/results_padded_pie')
        files = {
            'chord': base / ('Chord_Oracle5_FieldEnsemble/all_candidate_metrics.csv' if domain == 'PIE' else 'ChordEdit_Baseline/ensemble_results.csv'),
            'textsim': base / 'Chord_TextSim_FieldEnsemble/ensemble_results.csv',
            'cascade': base / 'Chord_TextSim_EditReward_FieldEnsemble/ensemble_results.csv'
        }
        data={}
        for method, path in files.items():
            rr=rows(path)
            if domain == 'PIE':
                rr=[r for r in rr if r['candidate_index']=='0'] if method=='chord' else [r for r in rr if r['n']=='100' and r['t']=='10' and float(r['beta'])==1]
            data[method]={r['sample_id']:r for r in rr}
            assert len(data[method]) == (700 if domain=='PIE' else 10160)
            sources[str(path)] = sha(path)
        assert set(data['chord'])==set(data['textsim'])==set(data['cascade'])
        if domain=='CropWeed':
            audit=json.loads((ROOT/'tmp/paper_final_review_20261008/audit.json').read_text())
            assert audit['verified']
            for method,name in [('chord','ChordEdit_Baseline'),('textsim','Chord_TextSim_FieldEnsemble'),('cascade','Chord_TextSim_EditReward_FieldEnsemble')]:
                assert sources[str(files[method])]==audit['methods'][name]['csv_sha256']
        else:
            audit=json.loads((ROOT/'tmp/paper_revision_20261003/audit.json').read_text())
            for path in files.values():
                assert sources[str(path)]==audit['sources'][str(path)]['sha256']
        tables[domain]={'all':{m:mean(list(rr.values())) for m,rr in data.items()},'groups':{}}
        if domain=='CropWeed':
            for family in ['weather','soil_type','leaf_amount']:
                tables[domain]['groups'][family]={m:mean([r for r in rr.values() if r['editing_type_id']==family]) for m,rr in data.items()}
        shortlist = json.loads((AUDIT/(domain+'_visual_shortlist.json')).read_text())
        records={r['id']:r for r in shortlist}
        for sid in SELECTED[domain]:
            r=records[sid]
            method_metrics={m:metrics(rr[sid]) for m,rr in data.items()}
            deltas={k:method_metrics['cascade'][k]-method_metrics['chord'][k] for k in METRICS}
            assert all(math.isfinite(v) for v in deltas.values())
            assert deltas['psnr_unedit']>0 and deltas['lpips_unedit_x1e3']<0 and deltas['clip_edited']>0
            assert sum(SIGN[i]*deltas[k]>0 for i,k in enumerate(METRICS))>=4
            assets={}; hashes={}
            for role, raw in zip(['source','chord','textsim','cascade'],r['paths']):
                p=Path(raw); dest=DIST/'assets/images'/f'{domain.lower()}-{sid}-{role}{p.suffix.lower()}'
                shutil.copy2(p,dest); assert sha(dest)==sha(p)
                assets[role]=dest.relative_to(DIST).as_posix(); hashes[role]={'source':str(p),'sha256':sha(p)}
            manifest=base/'Chord_TextSim_EditReward_FieldEnsemble/manifests'/(sid+'.json')
            man=json.loads(manifest.read_text()); out=next(x for x in man['outputs'] if x['n']==100 and x['t']==10 and float(x['beta'])==1)
            for k in METRICS:
                assert abs(float(out[k])-method_metrics['cascade'][k])<1e-9
            # PIE N1 image is the saved original Chord output reused in Figure 1.
            if domain=='PIE':
                bm=base/'Chord_Oracle3_FieldEnsemble/ensemble_results.csv'
                if '_baseline_index' not in locals():
                    _baseline_index={x['sample_id']:x for x in rows(bm) if x['n']=='1' and x.get('method')=='best_of_n'}
                    if len(_baseline_index)!=700:
                        _baseline_index={x['sample_id']:x for x in rows(bm) if x['n']=='1'}
                for k in METRICS:
                    a=float(_baseline_index[sid][k]); b=method_metrics['chord'][k]
                    assert abs(a-b)<1e-9,(sid,k,a,b)
            instruction=r['instruction'].split('. Preserve')[0].rstrip('.')
            if domain=='CropWeed':
                titles={'weather':'Lighting / weather','soil_type':'Soil appearance','leaf_amount':'Relative leaf amount'}
                category=titles[r['group']]
                change=edit_terms(r['source_prompt'],r['target_prompt'])
                title=f"{sid.split('_')[0]} · {change['before']} → {change['after']}"
            else:
                category={'0':'Mixed edits','1':'Object replacement','6':'Color changes'}.get(r['group'],'Other edits')
                change=edit_terms(r['source_prompt'],r['target_prompt'])
                title=instruction
            examples.append({'id':sid,'dataset':domain,'category':category,'title':title,'instruction':instruction,'sourcePrompt':r['source_prompt'],'targetPrompt':r['target_prompt'],'change':change,'images':assets,'metrics':method_metrics,'delta':deltas})
            provenance.append({'id':sid,'dataset':domain,'files':hashes,'manifest_sha256':sha(manifest),'metrics_match_saved_manifest':True,'baseline_metric_match':True})
    source=(PAPER/'main.tex').read_text(encoding='utf-8')
    abstract=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',source,re.S).group(1).strip().replace(r'\method','SearchChord').replace(r'\,',' ').replace('--','–')
    payload={'abstract':abstract,'examples':examples,'benchmarks':tables,'counts':{'PIE':{'semantic':700,'preservation':556},'CropWeed':{'total':10160,'weather':3387,'soil_type':3387,'leaf_amount':3386}},'selection':'Visually reviewed selected successes with gains in PSNR, LPIPS and CLIP-Edited, and at least four of five saved metrics. Not a random or representative benchmark subset.'}
    (DIST/'assets/data/results.json').write_text(json.dumps(payload,indent=2,allow_nan=False),encoding='utf-8')
    for name in ['fig3_scaling.png']:
        shutil.copy2(PAPER/'fig'/name,DIST/'assets'/name)
    (AUDIT/'asset_validation.json').write_text(json.dumps({'verified':True,'selected_per_dataset':{d:len(SELECTED[d]) for d in SELECTED},'saved_images_identical':True,'all_selected_joint_metric_gains':True,'input_hashes':sources,'examples':provenance,'paper_source_sha256':sha(PAPER/'main.tex'),'no_inference_launched':True},indent=2),encoding='utf-8')
    print(json.dumps({'examples':len(examples),'original_image_files':len(examples)*4,'verified':True}))
if __name__=='__main__':
    main()
