"""Read-only, source-first analytics. No imputation of missing costs or tax."""
from pathlib import Path
import io
import pandas as pd
import numpy as np
TABLES=['jobs','engineers','timesheets','materials','variations','subcontractors','job_expenses','invoices','payments','overheads']
NEEDED={'jobs':['JobID','Customer','JobType','Estimator','StartDate','EndDate','Status','QuotedHours','BudgetMaterials','QuotedRevenue'],'engineers':['EngineerID','Engineer','Role','BaseHourlyCost'],'timesheets':['JobID','EngineerID','WorkDate','Hours','ReturnVisitFlag','TravelHours'],'materials':['JobID','ActualMaterialCost','Supplier'],'variations':['JobID','ApprovedVariationRevenue','UnapprovedVariationValue'],'subcontractors':['JobID','SubcontractorCost'],'job_expenses':['JobID','OtherDirectCost'],'invoices':['InvoiceID','JobID','InvoiceDate','DueDate','NetAmount','VATRate'],'payments':['PaymentID','InvoiceID','PaymentDate','AmountGross'],'overheads':['Month','Category','NetCost','RecoverableVAT']}
UNIQUE={'jobs':'JobID','engineers':'EngineerID','invoices':'InvoiceID','payments':'PaymentID','materials':'JobID','variations':'JobID','subcontractors':'JobID','job_expenses':'JobID'}
NUMERIC={'jobs':['QuotedHours','BudgetMaterials','QuotedRevenue'],'engineers':['BaseHourlyCost'],'timesheets':['Hours','ReturnVisitFlag','TravelHours'],'materials':['ActualMaterialCost'],'variations':['ApprovedVariationRevenue','UnapprovedVariationValue'],'subcontractors':['SubcontractorCost'],'job_expenses':['OtherDirectCost'],'invoices':['NetAmount','VATRate'],'payments':['AmountGross'],'overheads':['NetCost','RecoverableVAT']}

def load(raw):
    f={name:pd.read_csv(io.BytesIO(raw[name])) for name in TABLES}
    for name,df in f.items():
        missing=set(NEEDED[name])-set(df.columns)
        if missing: raise ValueError(f'{name}.csv: missing {", ".join(sorted(missing))}')
        if name in UNIQUE:
            k=UNIQUE[name]
            if df[k].isna().any() or df[k].duplicated().any(): raise ValueError(f'{name}.csv: {k} must be unique and present')
        for c in NUMERIC[name]:
            df[c]=pd.to_numeric(df[c],errors='raise')
            if df[c].isna().any() or (df[c]<0).any(): raise ValueError(f'{name}.csv: {c} has missing or negative values')
    for table,col,parent in [('timesheets','JobID','jobs'),('timesheets','EngineerID','engineers'),('invoices','JobID','jobs'),('payments','InvoiceID','invoices'),('materials','JobID','jobs'),('variations','JobID','jobs'),('subcontractors','JobID','jobs'),('job_expenses','JobID','jobs')]:
        pk='EngineerID' if parent=='engineers' else 'InvoiceID' if parent=='invoices' else 'JobID'
        if not f[table][col].isin(f[parent][pk]).all():raise ValueError(f'{table}.csv contains {col} values absent from {parent}.csv')
    if (f['jobs'].QuotedHours<=0).any() or (f['jobs'].QuotedRevenue<=0).any():raise ValueError('Quoted hours and revenue must be positive')
    if (~f['timesheets'].ReturnVisitFlag.isin([0,1])).any():raise ValueError('ReturnVisitFlag must be 0 or 1')
    if (f['invoices'].VATRate>1).any():raise ValueError('VATRate must be decimal (e.g. 0.20)')
    for name,cols in [('jobs',['StartDate','EndDate']),('timesheets',['WorkDate']),('invoices',['InvoiceDate','DueDate']),('payments',['PaymentDate'])]:
        for c in cols:f[name][c]=pd.to_datetime(f[name][c],errors='raise')
    f['overheads']['Month']=pd.to_datetime(f['overheads']['Month'].astype(str)+'-01',errors='raise')
    return f

def analyse(f):
    labour=f['timesheets'].merge(f['engineers'],on='EngineerID',validate='many_to_one')
    # Recorded hourly rate only; not a fabricated payroll burden.
    labour['RecordedRateLabourCost']=labour.Hours*labour.BaseHourlyCost
    agg=labour.groupby('JobID',as_index=False).agg(ActualHours=('Hours','sum'),LabourCost=('RecordedRateLabourCost','sum'),ReturnFlags=('ReturnVisitFlag','sum'),TravelHours=('TravelHours','sum'))
    jobs=f['jobs'].merge(agg,on='JobID',how='left',validate='one_to_one')
    for name in ['materials','variations','subcontractors','job_expenses']:
        jobs=jobs.merge(f[name],on='JobID',how='left',validate='one_to_one')
    # A missing job-linked record is NOT assumed to be zero. Coverage tracked separately.
    for name,col in [('materials','ActualMaterialCost'),('variations','ApprovedVariationRevenue'),('subcontractors','SubcontractorCost'),('job_expenses','OtherDirectCost')]:
        jobs[name+'Present']=jobs.JobID.isin(f[name].JobID)
    jobs['LabourPresent']=jobs.JobID.isin(f['timesheets'].JobID)
    jobs['CompleteDirectRecords']=jobs[[name+'Present' for name in ['materials','variations','subcontractors','job_expenses']]+['LabourPresent']].all(axis=1)
    jobs['Revenue']=jobs.QuotedRevenue+jobs.ApprovedVariationRevenue
    jobs['RecordedDirectCost']=jobs.LabourCost+jobs.ActualMaterialCost+jobs.SubcontractorCost+jobs.OtherDirectCost
    jobs['RecordedContribution']=jobs.Revenue-jobs.RecordedDirectCost
    jobs['Margin']=100*jobs.RecordedContribution/jobs.Revenue
    jobs['ExtraHours']=jobs.ActualHours-jobs.QuotedHours
    jobs['MaterialsOverBudget']=jobs.ActualMaterialCost-jobs.BudgetMaterials
    jobs['Month']=jobs.EndDate.dt.to_period('M').astype(str)
    jobs['RecordStatus']=np.where(jobs.CompleteDirectRecords,'All required job tables present','Missing job records')
    return jobs,labour

def invoices(f,asof):
    inv=f['invoices'].copy()
    inv['Gross']=inv.NetAmount*(1+inv.VATRate)
    paid=f['payments'].groupby('InvoiceID',as_index=False).AmountGross.sum()
    inv=inv.merge(paid,on='InvoiceID',how='left',validate='one_to_one')
    inv['Paid']=inv.AmountGross.fillna(0)
    inv['Balance']=inv.Gross-inv.Paid
    inv['Overdue']=np.where((inv.DueDate<pd.Timestamp(asof))&(inv.Balance>0),inv.Balance,0)
    inv['Overpaid']=inv.Balance<-.01
    return inv

def monthly(jobs,f):
    # Completion-date grouping is operational analysis, NOT accounting revenue recognition.
    completed=jobs[(jobs.Status=='Completed')&jobs.CompleteDirectRecords]
    jobmonth=completed.groupby('Month',as_index=False).agg(CompletedJobValue=('Revenue','sum'),RecordedDirectCost=('RecordedDirectCost','sum'),RecordedContribution=('RecordedContribution','sum'),Jobs=('JobID','size'))
    overhead=f['overheads'].assign(Month=lambda d:d.Month.dt.to_period('M').astype(str)).groupby('Month',as_index=False).NetCost.sum().rename(columns={'NetCost':'RecordedOverheads'})
    result=overhead.merge(jobmonth,on='Month',how='outer').sort_values('Month')
    result['IndicativeDifference']=result.RecordedContribution-result.RecordedOverheads
    return result

def discover(jobs):
    c=jobs[(jobs.Status=='Completed')&jobs.CompleteDirectRecords].copy()
    findings=[]
    if c.empty:return findings
    losses=c[c.RecordedContribution<0]
    if len(losses):findings.append(dict(priority=1,headline=f'{len(losses)} completed jobs have negative recorded contribution',value=f'£{-losses.RecordedContribution.sum():,.0f}',detail='Start with the largest negative job balances. This uses recorded job costs and excludes unallocated costs.',basis=f'{len(losses)} of {len(c)} completed jobs',action='Review labour, materials, scope and source transactions for these jobs.',kind='Recorded finding'))
    over=c[c.ExtraHours>0]
    if len(over):findings.append(dict(priority=2,headline='Labour hours exceeded quoted allowances',value=f'{over.ExtraHours.sum():,.0f} h',detail=f'{len(over)} of {len(c)} jobs recorded more hours than quoted. This does not establish the cause or cash cost of the excess.',basis=f'{len(over)} jobs',action='Compare estimates with task records, scope changes and access delays.',kind='Recorded finding'))
    mat=c[c.MaterialsOverBudget>0]
    if len(mat):findings.append(dict(priority=3,headline='Materials exceeded quoted allowances',value=f'£{mat.MaterialsOverBudget.sum():,.0f}',detail=f'{len(mat)} jobs recorded higher material spending than their quote allowances.',basis=f'{len(mat)} jobs',action='Review material quantities, purchase prices and variations.',kind='Recorded finding'))
    for dimension in ['JobType','Estimator','Customer']:
        for key,g in c.groupby(dimension):
            if len(g)<10:continue
            rate=(g.ExtraHours>0).mean()
            overall=(c.ExtraHours>0).mean()
            if rate-overall>=.20:
                findings.append(dict(priority=4,headline=f'Labour overruns occur more often for {dimension.lower()} “{key}”',value=f'{rate:.0%}',detail=f'{(g.ExtraHours>0).sum()} of {len(g)} jobs exceeded quoted hours, versus {overall:.0%} across completed jobs. This is an association, not proof of responsibility.',basis=f'{len(g)} jobs in group',action='Compare similar jobs and investigate complexity, quote scope and assignment differences.',kind='Pattern to investigate'))
    return sorted(findings,key=lambda x:x['priority'])

# V5: comparison engine. Descriptive measures are separate from tested signals.
def comparison(jobs, dimension):
    c=jobs[(jobs.Status=='Completed') & jobs.CompleteDirectRecords].copy()
    if c.empty:
        return pd.DataFrame()
    c['LossFlag']=(c.RecordedContribution<0).astype(int)
    c['OverrunFlag']=(c.ExtraHours>0).astype(int)
    g=c.groupby(dimension,dropna=False).agg(
        Jobs=('JobID','size'), JobValue=('Revenue','sum'), DirectCosts=('RecordedDirectCost','sum'),
        Contribution=('RecordedContribution','sum'), LossJobs=('LossFlag','sum'),
        LabourOverrunJobs=('OverrunFlag','sum'), ExtraHours=('ExtraHours',lambda s:s.clip(lower=0).sum()),
        ReturnEntries=('ReturnFlags','sum'), MedianMargin=('Margin','median'),
        MedianJobValue=('Revenue','median'), MaterialOverspend=('MaterialsOverBudget',lambda s:s.clip(lower=0).sum())
    ).reset_index()
    g['MarginPct']=100*g.Contribution/g.JobValue
    g['LossSharePct']=100*g.LossJobs/g.Jobs
    g['LabourOverrunSharePct']=100*g.LabourOverrunJobs/g.Jobs
    g['AvgJobValue']=g.JobValue/g.Jobs
    return g.sort_values('JobValue',ascending=False)

def tested_patterns(jobs, dimension='JobType', min_jobs=12):
    """Two-proportion z tests + Benjamini-Hochberg correction; screening, not causality."""
    from math import erfc,sqrt
    c=jobs[(jobs.Status=='Completed') & jobs.CompleteDirectRecords].copy()
    if c.empty:return []
    results=[]
    for group, subset in c.groupby(dimension):
        others=c[c[dimension]!=group]
        if len(subset)<min_jobs or len(others)<min_jobs:continue
        for flag,metric in [('ExtraHours','Labour hours over quote'),('RecordedContribution','Negative job contribution')]:
            a=(subset[flag]>0) if flag=='ExtraHours' else (subset[flag]<0)
            b=(others[flag]>0) if flag=='ExtraHours' else (others[flag]<0)
            p1=float(a.mean());p2=float(b.mean());pooled=(a.sum()+b.sum())/(len(a)+len(b))
            se=sqrt(float(pooled*(1-pooled)*(1/len(a)+1/len(b))))
            pval=erfc(abs((p1-p2)/se)/sqrt(2)) if se else 1.
            results.append({'Group':str(group),'Dimension':dimension,'Measure':metric,'Jobs':len(subset),
                            'OtherJobs':len(others),'GroupRatePct':100*p1,'PeerRatePct':100*p2,
                            'DifferencePoints':100*(p1-p2),'PValue':pval,
                            'SupportingJobs':subset.loc[a,'JobID'].tolist()})
    # BH FDR correction across the entire search family, not per group.
    if not results:return []
    ordered=sorted(range(len(results)),key=lambda i:results[i]['PValue'])
    m=len(results);q=[1.]*m;lowest=1.
    for rank_index in range(m-1,-1,-1):
        idx=ordered[rank_index]
        lowest=min(lowest,results[idx]['PValue']*m/(rank_index+1))
        q[idx]=lowest
    for item,adj in zip(results,q):
        item['AdjustedP']=adj
        item['Evidence']='Statistically notable' if adj<.05 and abs(item['DifferencePoints'])>=10 else 'Descriptive only'
    return sorted(results,key=lambda x:(x['AdjustedP'],-abs(x['DifferencePoints'])))

def customer_invoices(f,asof):
    inv=invoices(f,asof)
    linked=inv.merge(f['jobs'][['JobID','Customer','JobType']],on='JobID',how='left',validate='many_to_one')
    return linked.groupby('Customer',as_index=False).agg(InvoicedNet=('NetAmount','sum'),OutstandingGross=('Balance',lambda s:s.clip(lower=0).sum()),OverdueGross=('Overdue','sum'),InvoiceCount=('InvoiceID','size'))
