"""Contractor Intelligence V5 — source-first management prototype.
Read-only. Synthetic demo is NEVER labelled verified. No provider API connection is implied.
"""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from engine import TABLES,load,analyse,invoices,monthly,comparison,tested_patterns,customer_invoices

st.set_page_config(page_title='Contractor Intelligence V5',page_icon='◈',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
html, body, [data-testid="stAppViewContainer"], .stApp {background:#f7f9fc!important;color:#172a43!important}
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li, [data-testid="stCaptionContainer"],
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
[data-testid="stRadio"] label, [data-testid="stCheckbox"] label,
[data-testid="stExpander"] summary, [data-testid="stTabs"] button,
[data-testid="stSelectbox"] label, [data-testid="stMultiSelect"] label {color:#172a43!important}
[data-testid="stCaptionContainer"] p, .stCaption {color:#52657c!important}
[data-testid="stSidebar"] *, [data-testid="stSidebar"] p {color:#172a43}
[data-testid="stMetricDelta"] {color:#172a43}
button, input, textarea {color:#172a43}
button[kind="primary"], button[kind="primary"] * {color:#ffffff!important}
[data-baseweb="select"] * {color:#172a43!important}
[data-testid="stDataFrame"] {color:#172a43}

[data-testid="stSidebar"]{background:#ffffff;border-right:1px solid #e5ebf2}
.block-container{max-width:1500px;padding-top:2rem;padding-bottom:5rem}
h1,h2,h3{color:#142840!important;letter-spacing:-.035em;font-weight:680!important}
h1{font-size:2.15rem!important} h3{font-size:1.2rem!important}
[data-testid="stMetric"]{background:white;border:1px solid #e4eaf2;padding:17px 19px;border-radius:14px;box-shadow:0 3px 14px rgba(20,40,70,.035)}
[data-testid="stMetricLabel"]{color:#62748a;font-size:.86rem}
[data-testid="stMetricValue"]{color:#152b47;font-size:1.75rem}
[data-testid="stExpander"]{background:white;border:1px solid #e4eaf2;border-radius:12px}
[data-testid="stDataFrame"]{border:1px solid #e4eaf2;border-radius:10px}
[data-testid="stAlert"]{border-radius:10px}
div[data-testid="stRadio"] label{font-weight:500}
.stButton button[kind="primary"]{background:#214d78;border-color:#214d78}
</style>''',unsafe_allow_html=True)
ROOT=Path(__file__).resolve().parent
BLUE='#346da0'; RED='#b75e61'; TEAL='#3a9487'; GOLD='#bd914a'
GBP=lambda n:'Unavailable' if pd.isna(n) else f'£{n:,.0f}'

def chart(fig,height=315):
    fig.update_layout(template='plotly_white',paper_bgcolor='white',plot_bgcolor='white',font=dict(color='#43556b',size=12),margin=dict(l=15,r=22,t=22,b=25),height=height,hoverlabel=dict(bgcolor='white'),showlegend=False)
    fig.update_xaxes(showgrid=False,title=None,automargin=True,zeroline=False)
    fig.update_yaxes(gridcolor='#edf1f5',title=None,automargin=True,zeroline=False)
    st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})

def heading(title,description=None):
    st.subheader(title)
    if description:st.caption(description)

def table(df,formats=None):
    if df.empty:st.info('No records match the selection.');return
    st.dataframe(df.style.format(formats or {},na_rep='—'),hide_index=True,use_container_width=True)

def simple_bars(df,category,value,colour=BLUE,percent=False):
    if df.empty:st.info('No records available.');return
    ordered=df.sort_values(value).copy()
    fig=px.bar(ordered,x=value,y=category,orientation='h',color_discrete_sequence=[colour],text=value)
    fig.update_traces(texttemplate='%{text:.1f}%' if percent else '£%{text:,.0f}',textposition='outside',cliponaxis=False)
    fig.update_xaxes(range=[min(0,float(ordered[value].min())*1.1),max(1,float(ordered[value].max())*1.26)])
    chart(fig,max(290,40*len(ordered)+100))

with st.sidebar:
    st.markdown('## ◈ Contractor Intelligence')
    st.caption('V5 · BUSINESS PERFORMANCE')
    st.divider()
    workspace=st.radio('Workspace',['Fictional demonstration','Import source files'])
    raw={}
    if workspace=='Fictional demonstration':
        raw={name:(ROOT/'data'/f'{name}.csv').read_bytes() for name in TABLES}
        st.warning('Synthetic example data — not a real business')
    else:
        st.caption('Upload the ten standardised CSV tables. The application does not substitute missing files with demo data.')
        for name in TABLES:
            upload=st.file_uploader(f'{name}.csv',type=['csv'],key=name)
            if upload:raw[name]=upload.getvalue()
        if len(raw)!=len(TABLES):
            st.info(f'{len(raw)} of {len(TABLES)} required tables supplied. Import templates are available in the package.')
            st.stop()
    st.divider()
    st.caption('INTEGRATIONS')
    st.write('CSV imports: available')
    st.caption('simPRO, Xero, Joblogic APIs: not connected')
    st.caption('No credentials are requested or stored.')

try:
    f=load(raw);jobs,labour=analyse(f)
    asof=max(f['jobs'].EndDate.max(),f['invoices'].InvoiceDate.max(),f['payments'].PaymentDate.max()).normalize()
    inv=invoices(f,asof)
    customer_finance=customer_invoices(f,asof)
    all_complete=jobs[(jobs.Status=='Completed')&jobs.CompleteDirectRecords].copy()
except Exception as exc:
    st.error(f'Data import failed validation: {exc}');st.stop()

st.title('Understand your business. Find what needs attention.')
st.caption('Job performance · Client profitability · Financial records · Evidence-backed investigations')
if workspace=='Fictional demonstration':
    st.warning('DEMONSTRATION — all records and figures are fictional. This is not verified company data.',icon='⚠️')
else:
    st.info('SOURCE FILES IMPORTED — figures reflect the uploaded records but are not independently verified. Review reconciliation and coverage before decisions.',icon='ℹ️')

with st.expander('Choose clients and types of work',expanded=False):
    x,y=st.columns(2)
    clients=x.multiselect('Clients',sorted(jobs.Customer.dropna().unique()),default=sorted(jobs.Customer.dropna().unique()))
    kinds=y.multiselect('Types of work',sorted(jobs.JobType.dropna().unique()),default=sorted(jobs.JobType.dropna().unique()))
selected=all_complete[all_complete.Customer.isin(clients)&all_complete.JobType.isin(kinds)].copy()
if selected.empty:st.warning('No completed jobs with complete direct records match the filters.');st.stop()

# Navigation uses named pages; each finding offers investigation controls.
page=st.radio('Explore',['Overview','Compare job types','Compare clients','Investigate jobs','Find patterns','People & finances','Data & connections','Ask a question'],horizontal=True,label_visibility='collapsed')
st.divider()

if page=='Overview':
    heading('Your company at a glance','Figures below cover selected completed jobs with required direct-cost records. They are not statutory accounting profit.')
    a,b,c,d=st.columns(4)
    a.metric('Completed job value',GBP(selected.Revenue.sum()))
    b.metric('Recorded job costs',GBP(selected.RecordedDirectCost.sum()))
    c.metric('Job contribution',GBP(selected.RecordedContribution.sum()))
    d.metric('Jobs losing money',f'{(selected.RecordedContribution<0).sum()} of {len(selected)}')
    st.caption('Job contribution excludes overheads and any employment costs not included in imported hourly rates. Do not treat it as company net profit.')
    heading('What needs your attention','Select an investigation from the menu to see the source jobs.')
    types=comparison(selected,'JobType');customers=comparison(selected,'Customer')
    losses=selected[selected.RecordedContribution<0]
    labour_over=selected[selected.ExtraHours>0]
    if len(losses):
        st.error(f'**{len(losses)} completed jobs recorded negative contribution**, totalling {GBP(-losses.RecordedContribution.sum())} in job-level losses. Review the largest losses in Investigate jobs.')
    if len(labour_over):
        st.warning(f'**{len(labour_over)} jobs exceeded quoted labour hours**, by {labour_over.ExtraHours.sum():,.0f} hours in total. This does not establish the cause or cash cost.')
    if len(types):
        low=types.sort_values('MarginPct').iloc[0]
        st.info(f'**{low.JobType} has the lowest aggregate job margin** among the selected work types ({low.MarginPct:.1f}% across {int(low.Jobs)} jobs). Compare job types to investigate.')
    left,right=st.columns(2)
    with left:
        heading('Profit margin by type of work','Job contribution as a percentage of recorded job value.')
        simple_bars(types,'JobType','MarginPct',TEAL,True)
    with right:
        heading('Job value by client','Turnover is not the same as profitability.')
        simple_bars(customers.head(10),'Customer','JobValue',BLUE)
    heading('What is still unavailable')
    st.info('Company operating profit, profit after tax and true cash balance are not shown: the source package does not prove complete payroll costs, accounting adjustments, tax liabilities or bank reconciliation.')

elif page=='Compare job types':
    heading('Which types of work make money?','Compare the value, profitability and delivery performance of different work categories.')
    g=comparison(selected,'JobType')
    if g.empty:st.stop()
    biggest=g.sort_values('Contribution',ascending=False).iloc[0]
    worst=g.sort_values('MarginPct').iloc[0]
    st.write(f'**What the records show:** {biggest.JobType} generated the most recorded job contribution ({GBP(biggest.Contribution)}). {worst.JobType} had the lowest contribution margin ({worst.MarginPct:.1f}%). Different job sizes and complexity can affect these comparisons.')
    a,b=st.columns(2)
    with a:
        heading('Profit margin by type of work','Higher means more of the job value remains after recorded direct costs.')
        simple_bars(g,'JobType','MarginPct',TEAL,True)
    with b:
        heading('Jobs that ran over quoted hours','Share of completed jobs in each work type.')
        simple_bars(g,'JobType','LabourOverrunSharePct',GOLD,True)
    heading('Compare the numbers')
    view=g.rename(columns={'JobType':'Type of work','Jobs':'Jobs','JobValue':'Job value','Contribution':'Job contribution','MarginPct':'Margin %','LossJobs':'Jobs losing money','LabourOverrunSharePct':'Jobs over hours %','ReturnEntries':'Return visit entries','MedianJobValue':'Typical job value'})
    table(view[['Type of work','Jobs','Job value','Job contribution','Margin %','Jobs losing money','Jobs over hours %','Return visit entries','Typical job value']],{'Job value':'£{:,.0f}','Job contribution':'£{:,.0f}','Margin %':'{:.1f}%','Jobs over hours %':'{:.1f}%','Typical job value':'£{:,.0f}'})
    pick=st.selectbox('Investigate a type of work',g.JobType.tolist())
    subset=selected[selected.JobType==pick].sort_values('RecordedContribution')
    st.write(f'**{pick}:** {len(subset)} completed jobs; {int((subset.RecordedContribution<0).sum())} recorded losses. The table below links each result to its job ID.')
    table(subset[['JobID','Customer','QuotedHours','ActualHours','ExtraHours','Revenue','RecordedDirectCost','RecordedContribution']].rename(columns={'Customer':'Client','QuotedHours':'Quoted hours','ActualHours':'Actual hours','ExtraHours':'Extra hours','Revenue':'Job value','RecordedDirectCost':'Recorded costs','RecordedContribution':'Contribution'}),{'Job value':'£{:,.0f}','Recorded costs':'£{:,.0f}','Contribution':'£{:,.0f}'})

elif page=='Compare clients':
    heading('Which clients are most profitable?','Look beyond turnover: compare margins, job losses, overruns and unpaid invoices.')
    g=comparison(selected,'Customer').merge(customer_finance,on='Customer',how='left')
    g=g.sort_values('JobValue',ascending=False)
    if g.empty:st.stop()
    top=g.iloc[0];lowest=g.sort_values('MarginPct').iloc[0]
    st.write(f'**What the records show:** {top.Customer} generated the most recorded job value ({GBP(top.JobValue)}). {lowest.Customer} has the lowest aggregate margin ({lowest.MarginPct:.1f}%, {int(lowest.Jobs)} jobs). Check job mix before drawing conclusions.')
    a,b=st.columns(2)
    with a:
        heading('Job value by client','Which clients generate the most work?')
        simple_bars(g.head(12),'Customer','JobValue',BLUE)
    with b:
        heading('Profit margin by client','Recorded job contribution as a percentage of job value.')
        simple_bars(g,'Customer','MarginPct',TEAL,True)
    heading('Client performance comparison')
    view=g.rename(columns={'Customer':'Client','Jobs':'Jobs','JobValue':'Job value','Contribution':'Contribution','MarginPct':'Margin %','LossJobs':'Loss-making jobs','LabourOverrunSharePct':'Jobs over hours %','OverdueGross':'Overdue invoices incl. VAT'})
    table(view[['Client','Jobs','Job value','Contribution','Margin %','Loss-making jobs','Jobs over hours %','Overdue invoices incl. VAT']],{'Job value':'£{:,.0f}','Contribution':'£{:,.0f}','Margin %':'{:.1f}%','Jobs over hours %':'{:.1f}%','Overdue invoices incl. VAT':'£{:,.0f}'})
    pick=st.selectbox('Investigate a client',g.Customer.tolist())
    sub=selected[selected.Customer==pick].sort_values('RecordedContribution')
    st.write(f'**{pick}:** {len(sub)} completed jobs. Compare the jobs below before concluding why margins differ.')
    table(sub[['JobID','JobType','Estimator','Revenue','ActualHours','ExtraHours','RecordedContribution','Margin']].rename(columns={'JobType':'Type of work','Estimator':'Estimator','Revenue':'Job value','ActualHours':'Actual hours','ExtraHours':'Extra hours','RecordedContribution':'Contribution','Margin':'Margin %'}),{'Job value':'£{:,.0f}','Contribution':'£{:,.0f}','Margin %':'{:.1f}%'})

elif page=='Investigate jobs':
    heading('Why did this job lose money?','See what the records prove, then investigate possible explanations.')
    sort=st.selectbox('Find jobs by',['Biggest losses first','Most hours over quote','Largest jobs'])
    ordered=selected.sort_values('RecordedContribution' if sort=='Biggest losses first' else 'ExtraHours' if sort=='Most hours over quote' else 'Revenue',ascending=sort=='Biggest losses first')
    jid=st.selectbox('Select a job',ordered.JobID.tolist(),format_func=lambda id:f'{id} · {ordered.loc[ordered.JobID==id,"Customer"].iloc[0]}')
    j=selected.set_index('JobID').loc[jid]
    st.write(f'**{j.Customer} · {j.JobType}** · Estimated by {j.Estimator}')
    a,b,c,d=st.columns(4)
    a.metric('Job value',GBP(j.Revenue));b.metric('Recorded costs',GBP(j.RecordedDirectCost));c.metric('Job contribution',GBP(j.RecordedContribution));d.metric('Labour hours',f'{j.ActualHours:.0f} / {j.QuotedHours:.0f}')
    left,right=st.columns(2)
    with left:
        heading('Where the job cost went','Recorded direct costs only.')
        parts=pd.DataFrame({'Cost':['Labour','Materials','Subcontractors','Other job costs'],'Amount':[j.LabourCost,j.ActualMaterialCost,j.SubcontractorCost,j.OtherDirectCost]})
        simple_bars(parts,'Cost','Amount',BLUE)
    with right:
        heading('What should we check?')
        if j.RecordedContribution<0:st.error(f'Recorded costs exceeded job value by {GBP(-j.RecordedContribution)}.')
        if j.ExtraHours>0:st.warning(f'{j.ExtraHours:.1f} hours over quote. Review estimating, scope changes, delays and timesheets.')
        if j.MaterialsOverBudget>0:st.warning(f'Materials cost {GBP(j.MaterialsOverBudget)} more than the quoted allowance.')
        if j.ReturnFlags>0:st.info(f'{int(j.ReturnFlags)} timesheet entries marked return visit; not proof of defects.')
        if j.UnapprovedVariationValue>0:st.info(f'{GBP(j.UnapprovedVariationValue)} of unapproved variation value; not counted as revenue.')
        if j.RecordedContribution>=0 and j.ExtraHours<=0 and j.MaterialsOverBudget<=0:st.success('No loss or labour/material overrun identified from the available job records.')
    with st.expander('See the supporting timesheets',expanded=True):
        entries=labour[labour.JobID==jid][['WorkDate','Engineer','Role','Hours','TravelHours','ReturnVisitFlag','BaseHourlyCost','RecordedRateLabourCost']].copy()
        entries.columns=['Date','Engineer','Role','Hours','Travel hours','Return flag','Recorded hourly rate','Cost at recorded rate']
        table(entries,{'Recorded hourly rate':'£{:,.2f}','Cost at recorded rate':'£{:,.2f}'})
        st.download_button('Download job timesheets',entries.to_csv(index=False).encode(),file_name=f'{jid}_timesheets.csv',mime='text/csv')

elif page=='Find patterns':
    heading('Patterns worth investigating','Statistical screening identifies associations, not proven causes. Small groups are excluded.')
    dimension=st.selectbox('Compare patterns across',['JobType','Customer','Estimator'],format_func=lambda x:{'JobType':'Types of work','Customer':'Clients','Estimator':'Estimators'}[x])
    findings=tested_patterns(selected,dimension)
    notable=[r for r in findings if r['Evidence']=='Statistically notable']
    st.write(f'**{len(notable)} statistically notable comparisons** found across {len(findings)} tests. Tests compare each group with the remaining jobs and apply a false-discovery-rate adjustment.')
    if not findings:st.info('Not enough comparable completed jobs to run these tests.')
    for r in findings[:15]:
        with st.expander(f"{r['Group']} · {r['Measure']} · {r['GroupRatePct']:.0f}% vs {r['PeerRatePct']:.0f}% · {r['Evidence']}"):
            st.write(f"**What we found:** {r['GroupRatePct']:.1f}% of {r['Jobs']} jobs in this group met the condition, compared with {r['PeerRatePct']:.1f}% across {r['OtherJobs']} other jobs.")
            st.caption(f"Adjusted p-value: {r['AdjustedP']:.3f}. This is a screening result, not a confidence score or causal explanation.")
            st.write('**Next step:** Compare similar job types, sizes, estimates and site conditions. Inspect supporting jobs before attributing responsibility.')
            st.code(', '.join(r['SupportingJobs'][:30]) or 'No matching job IDs')
    with st.expander('How the statistical checks work'):
        st.write('For groups with at least 12 jobs and 12 comparison jobs, the app tests differences in rates of labour overruns and negative job contribution using two-proportion z tests. Benjamini–Hochberg correction controls the expected false-discovery rate across tested comparisons. A difference of at least 10 percentage points and adjusted p < 0.05 is required for the “statistically notable” label. These tests do not adjust for all job-level confounders and are not proof of causation.')

elif page=='People & finances':
    heading('People and financial records','Workforce comparisons describe assignments, not individual fault or productivity.')
    staff=labour[labour.JobID.isin(selected.JobID)].groupby(['EngineerID','Engineer','Role'],as_index=False).agg(Hours=('Hours','sum'),Jobs=('JobID','nunique'),ReturnEntries=('ReturnVisitFlag','sum'),RateCost=('RecordedRateLabourCost','sum'))
    a,b=st.columns(2)
    with a:
        heading('Hours recorded by engineer','Workload depends on role, assignments and job complexity.')
        fig=px.bar(staff.sort_values('Hours'),x='Hours',y='Engineer',orientation='h',color_discrete_sequence=[BLUE]);chart(fig,450)
    with b:
        heading('Recorded overheads by category','Imported entries; not a complete accounting profit and loss statement.')
        oh=f['overheads'].groupby('Category',as_index=False).NetCost.sum()
        simple_bars(oh,'Category','NetCost',GOLD)
    with st.expander('Engineer records'):
        table(staff.rename(columns={'Hours':'Hours recorded','Jobs':'Jobs worked','ReturnEntries':'Return visit entries','RateCost':'Cost at imported rate'}),{'Cost at imported rate':'£{:,.0f}'})
    a,b,c=st.columns(3)
    a.metric('Invoiced excluding VAT',GBP(inv.NetAmount.sum()))
    b.metric('Outstanding incl. VAT',GBP(inv.Balance.clip(lower=0).sum()))
    c.metric('Overdue incl. VAT',GBP(inv.Overdue.sum()))
    st.caption(f'Overdue measured as at {asof:%d %B %Y} based on latest supplied records. No bank reconciliation or tax liability calculation.')
    with st.expander('Invoice records'):
        table(inv[['InvoiceID','JobID','NetAmount','Gross','Paid','Balance','Overdue']],{'NetAmount':'£{:,.0f}','Gross':'£{:,.0f}','Paid':'£{:,.0f}','Balance':'£{:,.0f}','Overdue':'£{:,.0f}'})

elif page=='Data & connections':
    heading('Where the information comes from','No live provider connection is claimed. This version accepts standardised read-only CSV exports.')
    st.info('simPRO, Joblogic, Xero, Sage and quotation-system API connectors are planned adapters, not functioning connections. Each provider requires its own authorisation, schema mapping and reconciliation tests.')
    a,b,c=st.columns(3)
    a.metric('Jobs in source',len(jobs));b.metric('Completed jobs with missing linked records',int(((jobs.Status=='Completed')&~jobs.CompleteDirectRecords).sum()));c.metric('Overpaid invoice flags',int(inv.Overpaid.sum()))
    st.write('**Import standard:** 10 tables, validated IDs and financial fields. Missing job-linked records are not silently treated as zero. Imported data is not independently certified.')
    st.write('**Source references:** JobID links job records to timesheets, costs and invoices; InvoiceID links invoices to payments. Raw tables can be inspected and downloaded below.')
    for name in TABLES:
        with st.expander(f'{name}.csv · {len(f[name])} rows'):
            st.dataframe(f[name].head(30),hide_index=True,use_container_width=True)
            st.download_button('Export source table',f[name].to_csv(index=False).encode(),file_name=f'{name}.csv',mime='text/csv',key=f'export_{name}')
    st.warning('Production readiness requires actual provider mappings, duplicate detection across overlapping systems, reviewed match approvals, secure multi-client storage and verified accounting reconciliations. These are not yet implemented.')

else:
    heading('Ask Contractor Intelligence','Choose a supported business question. Answers are calculated from the selected records, not invented by AI.')
    question=st.selectbox('What would you like to know?',[
        'Which client generates the most job value?',
        'Which client has the lowest job margin?',
        'Which type of work has the lowest job margin?',
        'Which type of work most often exceeds quoted hours?',
        'Which jobs have the largest recorded losses?',
        'How many completed jobs are loss-making?',
        'What is our net profit after tax?'])
    if st.button('Show answer',type='primary'):
        byclient=comparison(selected,'Customer');bytype=comparison(selected,'JobType')
        if question=='Which client generates the most job value?':
            r=byclient.sort_values('JobValue',ascending=False).iloc[0];st.success(f'{r.Customer} — {GBP(r.JobValue)} across {int(r.Jobs)} completed jobs.')
        elif question=='Which client has the lowest job margin?':
            r=byclient.sort_values('MarginPct').iloc[0];st.info(f'{r.Customer} — {r.MarginPct:.1f}% contribution margin across {int(r.Jobs)} jobs. Job mix may affect comparisons.')
        elif question=='Which type of work has the lowest job margin?':
            r=bytype.sort_values('MarginPct').iloc[0];st.info(f'{r.JobType} — {r.MarginPct:.1f}% contribution margin across {int(r.Jobs)} jobs.')
        elif question=='Which type of work most often exceeds quoted hours?':
            r=bytype.sort_values('LabourOverrunSharePct',ascending=False).iloc[0];st.info(f'{r.JobType} — {r.LabourOverrunSharePct:.1f}% of {int(r.Jobs)} jobs exceeded quoted hours.')
        elif question=='Which jobs have the largest recorded losses?':
            loss=selected[selected.RecordedContribution<0].nsmallest(10,'RecordedContribution')
            st.write(f'{len(loss)} largest recorded losses in the selected completed jobs:')
            table(loss[['JobID','Customer','JobType','RecordedContribution']].rename(columns={'Customer':'Client','JobType':'Type of work','RecordedContribution':'Contribution'}),{'Contribution':'£{:,.0f}'})
        elif question=='How many completed jobs are loss-making?':
            n=int((selected.RecordedContribution<0).sum());st.info(f'{n} of {len(selected)} completed jobs have negative recorded job contribution.')
        else:st.warning('Unavailable. These records do not establish complete accounting profit, taxable profit or actual tax liabilities. No estimate will be invented.')
        st.caption('Source: selected completed jobs with required direct-cost records. Check the supporting tables in Data & connections.')
    st.caption('Free-form AI chat is not implemented in this prototype. The supported question menu gives deterministic, traceable answers without unsupported claims.')

st.divider()
st.caption('CONTRACTOR INTELLIGENCE V5 · LOCAL PROTOTYPE · SYNTHETIC DEMO OR STANDARDISED CSV IMPORTS · NO LIVE API CONNECTIONS · NOT ACCOUNTING OR TAX ADVICE')
