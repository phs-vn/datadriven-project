from request_phs import *
from sklearn.cluster import KMeans
from scipy.stats import rankdata
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import matplotlib
from os.path import dirname, realpath
import itertools
matplotlib.use('Agg')


destination_dir = join(dirname(realpath(__file__)), 'result')

# Parameters:
centroids = 3
min_tickers = 3
nstd_bound = 2

start_time = time.time()

np.set_printoptions(linewidth=np.inf, precision=4, suppress=True,
                    threshold=sys.maxsize)
pd.set_option("display.max_rows", sys.maxsize,
              "display.max_columns", sys.maxsize,
              'display.expand_frame_repr', True)
pd.options.mode.chained_assignment = None

agg_data = fa.all('ins')  #################### expensive

quantities = ['ca', 'cl', 'cash', 'lib', 'asset', 'lt_loans', 'equity',
              'gprofit_ins', 'revenue_ins', 'net_income']

periods = fa.periods
tickers = fa.tickers('ins')

years = list()
quarters = list()
for period in periods:
    years.append(int(period[:4]))
    quarters.append(int(period[-1]))

period_tuple = list(zip(years,quarters))
inds = [x for x in itertools.product(period_tuple, tickers)]

for i in range(len(inds)):
    inds[i] = inds[i][0] + tuple([inds[i][1]])

index = pd.MultiIndex.from_tuples(inds, names=['year', 'quarter', 'ticker'])
col = pd.Index(quantities, name='quantity')

df = pd.DataFrame(columns=col, index=index)

for year, quarter in period_tuple:
    for ticker in tickers:
        for quantity in quantities:
            if quantity == 'ca':
                df.loc[(year, quarter, ticker), quantity] \
                    = agg_data.loc[(year, quarter, ticker),
                                   ('bs', 'A.I.')]
            elif quantity == 'cl':
                df.loc[(year, quarter, ticker), quantity] \
                    = -agg_data.loc[(year, quarter, ticker),
                                    ('bs', 'B.I.1.')]
            elif quantity == 'cash':
                df.loc[(year, quarter, ticker), quantity] \
                    = agg_data.loc[(year, quarter, ticker),
                                   ('bs', 'A.I.1.')]
            elif quantity == 'lib':
                df.loc[(year, quarter, ticker), quantity] \
                    = -agg_data.loc[(year, quarter, ticker),
                                    ('is', '7.1.')]
            elif quantity == 'pbt':
                df.loc[(year, quarter, ticker), quantity] \
                    = agg_data.loc[(year, quarter, ticker),
                                   ('is', '16.')]
            elif quantity == 'net_income':
                df.loc[(year, quarter, ticker), quantity] \
                    = agg_data.loc[(year, quarter, ticker),
                                   ('is','18.')]
            elif quantity == 'cur_asset':
                df.loc[(year, quarter, ticker), quantity] \
                    = agg_data.loc[(year, quarter, ticker),
                                   ('bs', 'A.I.')]
            elif quantity == 'cash':
                df.loc[(year, quarter, ticker), quantity] \
                    = agg_data.loc[(year, quarter, ticker),
                                   ('bs', 'A.I.1.')]
            elif quantity == 'ar':
                df.loc[(year, quarter, ticker), quantity] \
                    = agg_data.loc[(year, quarter, ticker),
                                   ('bs', 'A.I.3.')]
            elif quantity == 'inv':
                df.loc[(year, quarter, ticker), quantity] \
                    = agg_data.loc[(year, quarter, ticker),
                                   ('bs', 'A.I.4.')]
            elif quantity == 'ppe':
                df.loc[(year, quarter, ticker), quantity] \
                    = agg_data.loc[(year, quarter, ticker),
                                   ('bs', 'A.II.2.')]
            elif quantity == 'asset':
                df.loc[(year, quarter, ticker), quantity] \
                    = agg_data.loc[(year, quarter, ticker),
                                   ('bs', 'A.')]
            elif quantity == 'liability':
                df.loc[(year, quarter, ticker), quantity] \
                    = agg_data.loc[(year, quarter, ticker),
                                   ('bs', 'B.I.')]
            elif quantity == 'cur_liability':
                df.loc[(year, quarter, ticker), quantity] \
                    = agg_data.loc[(year, quarter, ticker),
                                   ('bs', 'B.I.1.')]
            elif quantity == 'lt_debt':
                df.loc[(year, quarter, ticker), quantity] \
                    = agg_data.loc[(year, quarter, ticker),
                                   ('bs', 'B.I.2.8.')]
            elif quantity == 'equity':
                df.loc[(year, quarter, ticker), quantity] \
                    = agg_data.loc[(year, quarter, ticker),
                                   ('bs', 'B.II.')]
            else:
                pass


del agg_data # for memory savings

df = df.loc[~(df==0).all(axis=1)]
df['cur_ratio'] = df['cur_asset'] / df['cur_liability']
df['quick_ratio'] = (df['cur_asset'] - df['inv']) / df['cur_liability']
df['cash_ratio'] = df['cash'] / df['cur_liability']
df['wc_turnover'] = df['revenue'] / (df['cur_asset'] - df['cur_liability'])
df['inv_turnover'] = df['cogs'] / df['inv']
df['ar_turnover'] = df['revenue'] / df['ar']
df['ppe_turnover'] = df['revenue'] / df['ppe']
df['(-)lib/asset'] = -df['liability'] / df['asset']
df['(-)lt_debt/equity'] = -df['lt_debt'] / df['equity']
df['gross_margin'] = df['gross_profit'] / df['revenue']
df['net_margin'] = df['net_income'] / df['revenue']
df['roe'] = df['net_income'] / df['equity']
df['roa'] = df['net_income'] / df['asset']

df['interest'] = df['interest'].replace(to_replace=0, value=1e3)
df['ebit/int'] = (df['pbt'] + df['interest']) / df['interest']

df = df.drop(columns=quantities)
df.sort_index(axis=1, inplace=True)
df.replace([np.inf, -np.inf], np.nan, inplace=True)

quantities_new = df.columns.to_list()

df.dropna(inplace=True, how='all')

sector_table = dict()
industry_list = dict()
ticker_list = dict()

ind_standards = list()
ind_levels = list()
ind_names = list()
for standard in standards:
    for level in fa.levels(standard):
        for industry in fa.industries(standard, int(level[-1])):
            ind_standards.append(standard)
            ind_levels.append(level)
            ind_names.append(industry)
kmeans_index = pd.MultiIndex.from_arrays([ind_standards,
                                          ind_levels,
                                          ind_names],
                                         names=['standard',
                                                'level',
                                                'industry'])
kmeans = pd.DataFrame(index = kmeans_index, columns = periods)
labels = pd.DataFrame(index = kmeans_index, columns = periods)
centers = pd.DataFrame(index = kmeans_index, columns = periods)
kmeans_tickers = pd.DataFrame(index = kmeans_index, columns = periods)
kmeans_coord = pd.DataFrame(index = kmeans_index, columns = periods)

# sector_table['standard_name'] -> return: DataFrame (Full table)
# industry_list[('standard_name', level)] -> return: list (all classification)
# ticker_list[('standard_name', level, 'industry')]
# -> return: list (all companies in a particular industry)

for standard in standards:
    sector_table[standard] = fa.classification(standard)
    sector_table[standard].columns \
        = pd.RangeIndex(start=1, stop=sector_table[standard].shape[1]+1)

    for level in sector_table[standard].columns:
        industry_list[(standard, level)] \
            = sector_table[standard][level].drop_duplicates().to_list()

        for industry in industry_list[standard, level]:
            ticker_list[(standard, level, industry)] \
                = sector_table[standard][level]\
                .loc[sector_table[standard][level]==industry]\
                .index.to_list()

            for year, quarter in zip(years, quarters):
                # cross section
                tickers = ticker_list[(standard, level, industry)]
                try:
                    df_xs = df.loc[(year, quarter, tickers), :]
                except KeyError:
                    continue
                df_xs.dropna(axis=0, how='any', inplace=True)
                if df_xs.shape[0] < min_tickers:
                    kmeans.loc[
                    (standard, standard + '_l' + str(level), industry), :] \
                        = None
                    labels.loc[
                    (standard, standard + '_l' + str(level), industry), :] \
                        = None
                    centers.loc[
                    (standard, standard + '_l' + str(level), industry), :] \
                        = None
                else:
                    for quantity in quantities_new:
                        # remove outliers (Interquartile Range Method)
                        ## (have to ensure symmetry)
                        df_xs_median = df_xs.loc[:, quantity].median()
                        df_xs_75q = df_xs.loc[:, quantity].quantile(q=0.75)
                        df_xs_25q = df_xs.loc[:, quantity].quantile(q=0.25)
                        cut_off = (df_xs_75q - df_xs_25q) * 1.5
                        for ticker in df_xs.index.get_level_values(2):
                            df_xs.loc[(year,quarter,ticker), quantity] \
                                = max(df_xs.loc[(year,quarter,ticker),
                                                quantity], df_xs_25q-cut_off)
                            df_xs.loc[(year,quarter,ticker), quantity] \
                                = min(df_xs.loc[(year,quarter,ticker),
                                                quantity], df_xs_75q+cut_off)

                        # standardize to mean=0
                        df_xs_mean = df_xs.loc[:, quantity].mean()
                        for ticker in df_xs.index.get_level_values(2):
                            df_xs.loc[(year,quarter,ticker), quantity] \
                                = (df_xs.loc[(year,quarter,ticker),
                                             quantity]
                                   - df_xs_mean)

                        # standardize to range (-1,1)
                        df_xs_min = df_xs.loc[:, quantity].min()
                        df_xs_max = df_xs.loc[:, quantity].max()
                        if df_xs_max == df_xs_min:
                            df_xs.drop(columns=quantity, inplace=True)
                        else:
                            for ticker in df_xs.index.get_level_values(2):
                                df_xs.loc[(year,quarter,ticker), quantity] \
                                    = -1 \
                                      + (df_xs.loc[(year,quarter,ticker),
                                                   quantity]
                                      - df_xs_min) / (df_xs_max-df_xs_min) * 2

                    # Kmeans algorithm
                    kmeans.loc[(standard,
                                standard+'_l'+str(level),
                                industry),
                               str(year) + 'q' + str(quarter)] \
                        = KMeans(n_clusters=centroids,
                                 init='k-means++',
                                 n_init=10,
                                 max_iter=1000,
                                 tol=1e-6,
                                 random_state=1)\
                        .fit(df_xs.dropna(axis=0, how='any'))

                    kmeans_tickers.loc[(standard,
                                        standard + '_l' + str(level),
                                        industry),
                                       str(year) + 'q' + str(quarter)] \
                        = df_xs.index.get_level_values(2).tolist()

                    kmeans_coord.loc[(standard, standard + '_l' + str(level),
                                     industry),
                                     str(year) + 'q' + str(quarter)] \
                        = df_xs.values

                    labels.loc[(standard,
                                standard + '_l' + str(level),
                                industry),
                                str(year) + 'q' + str(quarter)] \
                        = kmeans.loc[(standard,
                                      standard+'_l'+str(level),
                                      industry),
                                     str(year) + 'q' + str(quarter)].labels_\
                        .tolist()

                    centers.loc[(standard,
                                 standard + '_l' + str(level),
                                 industry),
                                str(year) + 'q' + str(quarter)] \
                        = kmeans.loc[(standard,
                                      standard+'_l'+str(level),
                                      industry),
                                     str(year) + 'q' + str(quarter)]\
                        .cluster_centers_.tolist()

del df_xs # for memory saving

radius_centers = pd.DataFrame(index=kmeans_index, columns=periods)
for row in range(centers.shape[0]):
    for col in range(centers.shape[1]):
        if centers.iloc[row,col] is None:
            radius_centers.iloc[row,col] = None
        else:
            distance = np.zeros(centroids)
            for center in range(centroids):
                # origin at (-1,-1,-1,...) whose dimension varies by PCA
                distance[center] = ((np.array(centers.iloc[row,col][center])
                                     - (-1))**2).sum()**(1/2)
            radius_centers.iloc[row,col] = distance

center_scores = pd.DataFrame(index=kmeans_index, columns=periods)
for row in range(centers.shape[0]):
    for col in range(centers.shape[1]):
        if radius_centers.iloc[row,col] is None:
            center_scores.iloc[row,col] = None
        else:
            center_scores.iloc[row,col] \
                = rankdata(radius_centers.iloc[row,col])
            for n in range(1, centroids+1):
                center_scores.iloc[row,col] = \
                    np.where(center_scores.iloc[row,col]==n,
                             100/(centroids+1)*n,
                             center_scores.iloc[row,col])

radius_tickers = pd.DataFrame(index=kmeans_index, columns=periods)
for row in range(labels.shape[0]):
    for col in range(labels.shape[1]):
        if labels.iloc[row,col] is None:
            radius_tickers.iloc[row,col] = None
        else:
            distance = np.zeros(len(labels.iloc[row,col]))
            for ticker in range(len(labels.iloc[row,col])):
                # origin at (-1,-1,-1,...) whose dimension varies by PCA
                distance[ticker] \
                    = (((np.array(kmeans_coord.iloc[row,col][ticker]))
                        - (-1))**2).sum()**(1/2)
            radius_tickers.iloc[row,col] = distance

ticker_raw_scores = pd.DataFrame(index=kmeans_index, columns=periods)#not used
for row in range(labels.shape[0]):
    for col in range(labels.shape[1]):
        if labels.iloc[row,col] is None:
            ticker_raw_scores.iloc[row,col] = None
        else:
            raw = np.zeros(len(labels.iloc[row,col]))
            for n in range(len(labels.iloc[row,col])):
                raw[n] = center_scores.iloc[row,col][labels.iloc[row,col][n]]
            ticker_raw_scores.iloc[row,col] = raw

ticker_scores = pd.DataFrame(index=kmeans_index, columns=periods)
for row in range(radius_tickers.shape[0]):
    for col in range(radius_tickers.shape[1]):
        if radius_tickers.iloc[row,col] is None:
            ticker_scores.iloc[row,col] = None
        else:
            min_ = min(radius_centers.iloc[row, col])
            max_ = max(radius_centers.iloc[row, col])
            range_ = max_ - min_
            f = interp1d(np.sort(np.append(radius_centers.iloc[row,col],
                                           [min_-range_/(centroids-1),
                                            max_+range_/(centroids-1)])),
                         np.sort(np.append(center_scores.iloc[row,col],
                                           [0,100])),
                         kind='linear', bounds_error=False, fill_value=(0,100))
            ticker_scores.iloc[row,col] = f(radius_tickers.iloc[row,col])
            for n in range(len(ticker_scores.iloc[row,col])):
                ticker_scores.iloc[row, col][n] \
                    = int(ticker_scores.iloc[row, col][n])

ind_standards = list()
ind_levels = list()
ind_names = list()
ind_tickers = list()
ind_periods = list()
for standard in standards:
    for level in fa.levels(standard):
        for industry in fa.industries(standard, int(level[-1])):
            for period in periods:
                try:
                    if isinstance(kmeans_tickers.loc[
                                      (standard,level,industry),period],
                                  str) is True:
                        ind_standards.append(standard)
                        ind_levels.append(level)
                        ind_names.append(industry)
                        ind_tickers.append(
                            kmeans_tickers.loc[
                                (standard,level,industry),period])
                        ind_periods.append(period)
                    else:
                        for ticker in kmeans_tickers.loc[
                            (standard,level,industry),period]:
                            ind_standards.append(standard)
                            ind_levels.append(level)
                            ind_names.append(industry)
                            ind_tickers.append(ticker)
                            ind_periods.append(period)

                except TypeError:
                    continue

result_index = pd.MultiIndex.from_arrays([ind_standards,
                                          ind_levels,
                                          ind_names,
                                          ind_tickers,
                                          ind_periods],
                                         names=['standard',
                                                'level',
                                                'industry',
                                                'ticker',
                                                'period'])

result_table = pd.DataFrame(index=result_index, columns=['credit_score'])
for standard in standards:
    for level in fa.levels(standard):
        for industry in fa.industries(standard, int(level[-1])):
            for period in periods:
                try:
                    for n in range(len(kmeans_tickers.loc[
                                           (standard,level,industry),period])):
                        result_table.loc[
                            (standard,
                             level,
                             industry,
                             kmeans_tickers.loc[
                                 (standard, level, industry), period][n],
                             period)] \
                            = ticker_scores.loc[(standard,level,industry),
                                                period][n]
                except TypeError:
                    continue

result_table = result_table.unstack(level=4)
result_table.columns = result_table.columns.droplevel(0)

#==============================================================================

component_filename = 'component_talbe'
def export_component_table():
    global destination_dir
    global df
    df.to_csv(join(destination_dir, component_filename+'.csv'))

export_component_table()
df = pd.read_csv(join(destination_dir, component_filename+'.csv'),
                 index_col=['year','quarter','ticker'])

result_filename = 'result_table'
def export_result_table():
    global destination_dir
    global result_table
    result_table.to_csv(join(destination_dir, result_filename+'.csv'))

export_result_table()
result_table = pd.read_csv(join(destination_dir, result_filename+'.csv'),
                           index_col=['standard','level','industry','ticker'])

def graph_ticker(ticker: str, standard: str, level: int):
    table = pd.DataFrame(index=['credit_score'],
                         columns=periods)

    table.loc['credit_score', periods] \
        = result_table.xs(key=(standard, standard + '_l' + str(level)),
                          axis=0, level=[0,1])\
        .xs(key=ticker, axis=0, level=1).values

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8,6))
    ax.set_title(ticker + '\n' + standard.upper()
                 + ' Level {} Classification'.format(level),
                 fontsize=15, fontweight='bold', color='darkslategrey',
                 fontfamily='Times New Roman')

    xloc = np.arange(table.shape[1]) # label locations
    rects = ax.bar(xloc, table.iloc[0], width=0.8,
                   color='tab:blue', label='Credit Score', edgecolor='black')
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{:.0f}'.format(height),
                    xy=(rect.get_x()+rect.get_width()/2, height),
                    xytext=(0,3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=11)

    ax.set_xticks(np.arange(len(xloc)))
    ax.set_xticklabels(table.columns.tolist(), rotation=45, x=xloc,
                       fontfamily='Times New Roman', fontsize=11)

    ax.set_yticks(np.array([0,25,50,75,100]))
    ax.tick_params(axis='y', labelcolor='black', labelsize=11)

    Acolor = 'green'
    Bcolor = 'olivedrab'
    Ccolor = 'darkorange'
    Dcolor = 'firebrick'

    ax.axhline(100, ls='--', linewidth=0.5, color=Acolor)
    ax.axhline(75, ls='--', linewidth=0.5, color=Bcolor)
    ax.axhline(50, ls='--', linewidth=0.5, color=Ccolor)
    ax.axhline(25, ls='--', linewidth=0.5, color=Dcolor)
    ax.fill_between([-0.4,xloc[-1]+0.4], 100, 75,
                    color=Acolor, alpha=0.2)
    ax.fill_between([-0.4,xloc[-1]+0.4], 75, 50,
                    color=Bcolor, alpha=0.25)
    ax.fill_between([-0.4,xloc[-1]+0.4], 50, 25,
                    color=Ccolor, alpha=0.2)
    ax.fill_between([-0.4,xloc[-1]+0.4], 25, 0,
                    color=Dcolor, alpha=0.2)

    plt.xlim(-0.6, xloc[-1] + 0.6)

    ax.set_ylim(top=110)
    midpoints = np.array([87.5, 62.5, 37.5, 12.5])/110
    labels = ['Group A', 'Group B', 'Group C', 'Group D']
    colors = [Acolor, Bcolor, Ccolor, Dcolor]
    for loc in zip(midpoints, labels, colors):
        ax.annotate(loc[1],
                    xy=(-0.1, loc[0]),
                    xycoords='axes fraction',
                    textcoords="offset points",
                    xytext=(0,-5),
                    ha='center', va='bottom',
                    color=loc[2], fontweight='bold',
                    fontsize='large')

    ax.legend(loc='best', framealpha=5)
    ax.margins(tight=True)
    plt.subplots_adjust(left=0.15, bottom=0.1, right=0.95, top=0.9)
    plt.savefig(join(destination_dir, f'{ticker}_result.png'))


def graph_crash(benchmark:float, standard:str, level:int,
                period:str, segment:str , exchange:str='HOSE'):
    crash_list = ta.crash(benchmark, period, segment, exchange)
    for ticker in crash_list:
        try:
            graph_ticker(ticker, standard, level)
            plt.savefig(join(destination_dir,
                             f'crash_{period}_{ticker}_result.png'),
                        bbox_inches='tight')
        except KeyError:
            continue


def graph_all(standard:str, level:int):
    global tickers
    for ticker in tickers:
        try:
            graph_ticker(ticker, standard, level)
        except KeyError:
            pass


def breakdown(ticker:str):
    table = df.xs(ticker, axis=0, level=2)
    num_quantities = table.shape[1]
    fig = plt.subplots(num_quantities, 1,
                       figsize=(6,14), sharex=True)
    plt.suptitle(f'Raw Component Movement: {ticker}', x=0.52, ha='center',
                 fontweight='bold', color='darkslategrey',
                 fontfamily='Times New Roman', fontsize=17)
    colors = plt.rcParams["axes.prop_cycle"]()
    for i in range(num_quantities):
        yval = table[table.columns[i]].values
        while len(yval) < len(fa.periods):
            yval = np.insert(yval, 0, np.nan)
        fig[1][i].plot(periods, yval,
                       color=next(colors)["color"])
        fig[1][i].grid(True, which='both', axis='x', alpha=0.6)
        fig[1][i].margins(tight=True)
        fig[1][i].set_yticks([])
        fig[1][i].set_ylabel(table.columns[i], labelpad=1,
                             ha='center', fontsize=8.5)

    plt.subplots_adjust(left=0.05,
                        right=0.98,
                        bottom=0.04,
                        top=0.95,
                        hspace=0.1)
    plt.xticks(rotation=45, fontfamily='Times New Roman', fontsize=11)
    plt.savefig(join(destination_dir, f'{ticker}_components'))


def breakdown_all(segment:str, exchange:str):
    for ticker in fa.tickers(segment, exchange):
        try:
            breakdown(ticker)
        except KeyError:
            pass

def compare_industry(ticker:str, standard:str, level:int):

    full_list = fa.classification(standard).iloc[:,level-1]
    industry = full_list.loc[ticker]
    peers = full_list.loc[full_list == industry].index.tolist()

    table = df.loc[df.index.get_level_values(2).isin(peers)]
    table.dropna(axis=0, how='all', inplace=True)

    median = table.groupby(axis=0, level=[0,1]).median()
    # to avoid cases of missing data right at the first period, result in mis-shaped
    quantities = pd.DataFrame(np.zeros_like(median),
                              index=median.index,
                              columns=median.columns)
    ref_table = table.xs(ticker, axis=0, level=2)
    quantities = pd.concat([quantities, ref_table], axis=0)
    quantities = quantities.groupby(level=[0,1], axis=0).sum()

    comparison = pd.concat([quantities, median], axis=1, join='outer',
                           keys=[ticker, 'median'])

    fig, ax = plt.subplots(3,5, figsize=(18,8),
                           tight_layout=True)

    periods = [str(q[0]) + 'q' + str(q[1]) for q in comparison.index]
    variables \
        = comparison.columns.get_level_values(1).drop_duplicates().to_numpy()
    variables = np.append(variables, None)
    variables = np.reshape(variables, (3,5))
    for row in range(3):
        for col in range(5):
            w = 0.35
            l = np.arange(len(periods))  # the label locations
            if variables[row,col] is None:
                ax[row, col].axis('off')
            else:
                ax[row,col].bar(l-w/2, quantities.iloc[:, row*5+col],
                                width=w, label=ticker,
                                color='tab:orange', edgecolor='black')
                ax[row,col].bar(l+w/2, median.iloc[:, row*5+col],
                                width=w, label='Industry\'s Average',
                                color='tab:blue', edgecolor='black')
                plt.setp(ax[row,col].xaxis.get_majorticklabels(), rotation=45)
                ax[row,col].set_xticks(l)
                ax[row,col].set_xticklabels(periods, fontsize=7)
                ax[row, col].set_yticks([])
                ax[row,col].set_autoscaley_on(True)
                ax[row,col].set_title(variables[row,col], fontsize=9)

    fig.suptitle(f'{ticker} \n Comparison with the industry\'s average',
                 fontweight='bold', color='darkslategrey',
                 fontfamily='Times New Roman', fontsize=14)
    handles, labels = ax[0,0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper left',
               bbox_to_anchor=(0.01, 0.98), ncol=2, fontsize=9,
               markerscale=0.7)
    plt.savefig(join(destination_dir, f'{ticker}_compare_industry.png'))


def compare_rs(tickers: list, standard: str, level: int):

    rs_file = join(dirname(realpath(__file__)), 'research_rating.xlsx')
    rs_rating = pd.read_excel(rs_file, sheet_name='summary',
                              index_col='ticker', engine='openpyxl')

    def scoring(rating: str) -> int:
        mapping = {'AAA': 95, 'AA': 85, 'A': 77.5,
                   'BBB': 72.5, 'BB': 67.5, 'B': 62.5,
                   'CCC': 57.5, 'CC': 52.5, 'C': 47.5,
                   'DDD': 40, 'DD': 30, 'D': 20}
        try:
            return mapping[rating]
        except KeyError:
            return np.nan

    rs_rating = rs_rating.applymap(scoring)
    for i in range(rs_rating.shape[0]):
        for j in range(1, rs_rating.shape[1] - 1):
            before = rs_rating.iloc[i, j - 1]
            after = np.nan
            k = 0
            if not np.isnan(before) and np.isnan(rs_rating.iloc[i, j]):
                while np.isnan(after):
                    k += 1
                    after = rs_rating.iloc[i, j+k]
                rs_rating.iloc[i, j] = before + (after-before)/(k+1)

    model_file = join(dirname(realpath(__file__)),
                      'result', 'result_table.csv')
    model_rating = pd.read_csv(model_file, index_col='ticker')
    model_rating \
        = model_rating.loc[model_rating['standard'] == standard]
    model_rating \
        = model_rating.loc[
        model_rating['level'] == standard + '_l' + str(level)]
    model_rating.drop(columns=['standard', 'level', 'industry'], inplace=True)

    for ticker in tickers:
        try:
            fig, ax = plt.subplots(1, 1, figsize=(8, 6))
            periods = [q for q in model_rating.columns]
            w = 0.35
            xloc = np.arange(len(periods))  # the label locations
            ax.bar(xloc - w / 2, model_rating.loc[ticker, :],
                   width=w, label='K-Means',
                   color='tab:blue', edgecolor='black')
            ax.bar(xloc + w / 2, rs_rating.loc[ticker, :],
                   width=w, label='Research\'s Rating',
                   color='tab:gray', edgecolor='black')
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            ax.set_xticks(xloc)
            ax.set_xticklabels(periods, fontsize=11)

            ax.set_yticks(np.array([0, 25, 50, 75, 100]))
            ax.tick_params(axis='y', labelcolor='black', labelsize=11)

            Acolor = 'green'
            Bcolor = 'olivedrab'
            Ccolor = 'darkorange'
            Dcolor = 'firebrick'

            ax.axhline(100, ls='--', linewidth=0.5, color=Acolor)
            ax.axhline(75, ls='--', linewidth=0.5, color=Bcolor)
            ax.axhline(50, ls='--', linewidth=0.5, color=Ccolor)
            ax.axhline(25, ls='--', linewidth=0.5, color=Dcolor)
            ax.fill_between([-0.4, xloc[-1] + 0.4], 100, 75,
                            color=Acolor, alpha=0.2)
            ax.fill_between([-0.4, xloc[-1] + 0.4], 75, 50,
                            color=Bcolor, alpha=0.25)
            ax.fill_between([-0.4, xloc[-1] + 0.4], 50, 25,
                            color=Ccolor, alpha=0.2)
            ax.fill_between([-0.4, xloc[-1] + 0.4], 25, 0,
                            color=Dcolor, alpha=0.2)

            plt.xlim(-0.6, xloc[-1] + 0.6)

            ax.set_ylim(top=110)
            midpoints = np.array([87.5, 62.5, 37.5, 12.5]) / 110
            labels = ['Group A', 'Group B', 'Group C', 'Group D']
            colors = [Acolor, Bcolor, Ccolor, Dcolor]
            for loc in zip(midpoints, labels, colors):
                ax.annotate(loc[1],
                            xy=(-0.1, loc[0]),
                            xycoords='axes fraction',
                            textcoords="offset points",
                            xytext=(0, -5),
                            ha='center', va='bottom',
                            color=loc[2], fontweight='bold',
                            fontsize='large')
            ax.legend(loc='best', framealpha=5)
            ax.margins(tight=True)
            plt.subplots_adjust(left=0.15, bottom=0.1, right=0.95, top=0.9)
            ax.set_title(ticker + '\n' + "Comparison with Research's Rating",
                         fontsize=15, fontweight='bold', color='darkslategrey',
                         fontfamily='Times New Roman')
            plt.savefig(join(destination_dir, f'{ticker}_compare_rs.png'))
        except KeyError:
            print(f'{ticker} has KeyError')


def mlist_group(standard:str, level:int, year:int, quarter:int) -> dict:

    file = join(dirname(realpath(__file__)),
                'result', 'result_table.csv')
    table = pd.read_csv(file, index_col='ticker')

    table = table.loc[table['standard'] == standard]
    table = table.loc[table['level'] == standard + '_l' + str(level)]
    table.drop(columns=['standard', 'level', 'industry'], inplace=True)

    series = table[str(year) + 'q' + str(quarter)]
    mlist = internal.mlist('all')
    fin_tickers = fa.fin_tickers(False)
    ticker_list = [ticker for ticker in mlist if ticker not in fin_tickers]
    # some tickers in margin list do not have enough data to run K-Means
    model_tickers = table.index.to_list()
    ticker_list = list(set(ticker_list).intersection(model_tickers))
    series = series.loc[ticker_list]

    def f(score):
        if score <= 25:
            return 'D'
        elif score <= 50:
            return 'C'
        elif score <= 75:
            return 'B'
        elif score <= 100:
            return 'A'
        else:
            return np.nan

    series = series.map(f).dropna()
    groups = series.drop_duplicates().to_numpy()
    d = dict()
    for group in groups:
        tickers = series.loc[series==group].index.to_list()
        d[group] = tickers

    return d


# Output results
#graph_all('gics', 1)
#graph_crash(-0.5, 'gics', 1, '2020q3', 'gen', 'HOSE')
#breakdown_all('gen')


execution_time = time.time() - start_time
print(f"The execution time is: {int(execution_time)}s seconds")