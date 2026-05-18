"""Pre-weekend forecast from earlier race results only; no target-race inputs."""
from datetime import date
import random
import math
from models import finite, fit_ridge, predict, mean
FEATURES=['driver_last_5_mean_finish','team_last_10_mean_finish','driver_last_5_podium_rate']

def iso(value):
    return date.fromisoformat(str(value))

def feature_vector(driver,team,prior):
    own=[r['finish'] for race in prior for r in race['results'] if r['driver']==driver][-5:]
    constructor=[r['finish'] for race in prior for r in race['results'] if r['team']==team][-10:]
    return [mean(own) if own else 10.5,mean(constructor) if constructor else 10.5,mean([float(p<=3) for p in own]) if own else .15]

def validate(data):
    cutoff=iso(data['as_of']);target=data['target'];target_date=iso(target['date'])
    if cutoff>=target_date:raise ValueError('as_of must precede the target race')
    races=data['races'];entrants=data['entrants']
    if not 8<=len(races)<=100:raise ValueError('Supply 8–100 historical races')
    if not 3<=len(entrants)<=30:raise ValueError('Supply 3–30 entrants')
    previous=None;seen=set()
    for race in races:
        day=iso(race['date'])
        if day>=cutoff:raise ValueError('Historical race on or after cutoff rejected: '+race['name'])
        if previous and day<=previous:raise ValueError('Races must be unique and ordered oldest first')
        season=int(race.get('season',day.year))
        target_season=int(target.get('season',target_date.year))
        if season!=day.year or target_season!=target_date.year:raise ValueError('Season must match race date')
        if (season,race['round'])>=(target_season,target['round']):raise ValueError('Target or later round must not be included')
        previous=day
        key=(day,race['round'])
        if key in seen:raise ValueError('Duplicate race')
        seen.add(key)
        results=race['results']
        if not 3<=len(results)<=30:raise ValueError('Each race requires 3–30 results')
        ids=[r['driver'] for r in results];finishes=[finite(r['finish']) for r in results]
        if len(set(ids))!=len(ids):raise ValueError('Duplicate driver in race')
        if any(p!=int(p) or not 1<=p<=30 for p in finishes) or len(set(finishes))!=len(finishes):
            raise ValueError('Finishing positions must be unique integers from 1 to 30')
        for r in results:
            if not isinstance(r['driver'],str) or not isinstance(r['team'],str):raise ValueError('Driver and team must be strings')
    ids=[r['driver'] for r in entrants]
    if len(set(ids))!=len(ids):raise ValueError('Entrant driver IDs must be unique')
    for r in entrants:
        if not isinstance(r['team'],str):raise ValueError('Entrant team must be a string')
    if any(k in r for r in entrants for k in ['finish','grid','practice_gap','points']):
        raise ValueError('Entrants must not contain target-race outcomes or weekend features')
    return races,entrants

def training_rows(races):
    rows=[]
    # Three warmup races initialize lagged form; each row uses only earlier races.
    for index,race in enumerate(races):
        if index<3:continue
        for r in race['results']:
            rows.append({'race':race['name'],'date':race['date'],'driver':r['driver'],'x':feature_vector(r['driver'],r['team'],races[:index]),'y':r['finish']})
    return rows

def run(data):
    races,entrants=validate(data)
    count=int(data.get('simulations',5000))
    if not 100<=count<=50000:raise ValueError('Simulations must be 100–50000')
    rows=training_rows(races)
    split_date=races[max(5,int(len(races)*.75))]['date']
    train=[r for r in rows if r['date']<split_date];test=[r for r in rows if r['date']>=split_date]
    model=fit_ridge([r['x'] for r in train],[r['y'] for r in train],2)
    errors=[r['y']-predict(model,r['x']) for r in test]
    sigma=max(.5,math.sqrt(mean([e*e for e in errors])))
    final=fit_ridge([r['x'] for r in rows],[r['y'] for r in rows],2)
    expected=[predict(final,feature_vector(r['driver'],r['team'],races)) for r in entrants]
    rng=random.Random(int(data.get('seed',42)));wins=[0]*len(entrants);podium=[0]*len(entrants)
    for _ in range(count):
        order=sorted(range(len(entrants)),key=lambda i:expected[i]+rng.gauss(0,sigma))
        wins[order[0]]+=1
        for i in order[:3]:podium[i]+=1
    output=[{'driver':r.get('name',r['driver']),'predicted_finish_score':expected[i],'win_probability':wins[i]/count,'podium_probability':podium[i]/count,'win_monte_carlo_standard_error':math.sqrt((wins[i]/count)*(1-wins[i]/count)/count)} for i,r in enumerate(entrants)]
    output.sort(key=lambda r:-r['win_probability'])
    return {'metrics':{'Held-out finish MAE':mean([abs(e) for e in errors]),'Recent-form baseline MAE':mean([abs(r['y']-r['x'][0]) for r in test]),'Simulation count':count,'Historical races':len(races)},'series':{},'rows':output,'details':{'historical_as_of':data['as_of'],'target_race':data['target'],'latest_included_race':races[-1]['name'],'latest_included_date':races[-1]['date'],'features':FEATURES,'noise_sigma':sigma,'held_out_races':list(dict.fromkeys(r['race'] for r in test)),'training_rows':len(train),'held_out_rows':len(test),'final_training_rows':len(rows),'provenance':data.get('provenance',{}),'method':'Ridge, fixed penalty 2. Feature history updates through each earlier completed race; holdout weights stay fixed. Refit on all pre-cutoff rows for target. All races in input must precede cutoff. No target grid, practice, race outcomes or later race results.','assumptions':'Independent Gaussian finish-score noise; simulation probabilities are not calibrated odds. No explicit weather, pit stop, circuit or DNF model. The entrant list is assumed, not an archived entry-list verification.'}}
