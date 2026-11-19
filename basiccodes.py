
# 
np.linspace(0, 1, 10) # generate 10 numbers from 0 to 1
".".join(["abc", "def"]) # paste() return "abc.def"
re.sub(r"sample", "new", text) # replace the text
df['First4'] = df['Words'].str[:4]
np.tan(np.radians(3.5)) * 10 * 2 # calculate beam diameter at 10m range
str.zfill(width) # add zero if the string is less than 'width'
dt.year
df['A'] = np.where(df['A'] < 0, 0, df['A']) # replace number to 0
df.iloc[:, :3] # show first 3 columns
text.split('_')[0] # retreive first component from the string "text" which is separated with "_". text = "SD1031_0501", then retreive "SD1031"



# dataframe
new_df = df[df['column'].str.contains('word1|word2')] # subset by category column which include 'word1|word2'
new_df = df[df['column'].isin(['word1', 'word2'])] # subset by category column which are exactly equal to 'word1', 'word2'
df = df.drop(columns='column_name') # remove a column
df = df.drop_duplicates() # drop duplicates
df = df.drop_duplicates(subset=['column_name1', 'column_name2'])
df = df.rename(columns={'old': 'new'})
df_cleaned = df.dropna(subset=['col2']) #remove na
df[df['col'].isnull()] # rows which is na in "col"
new_df = original_df[['col1', 'col2']].copy()
df['col'].str.replace('Z', '') # remove "Z" from the str
df['Platform'] = df['Platform'].cat.remove_unused_categories() # remove unappeared Platform completely (statsmodels retains all historical or declared categories defined in the DataFrame column)
np.diff(my_array) # diff between consecutive elements
df['category_col'].value_counts().head(10) # counts rows for each category and show the top 10 most count
df['category_col'].value_counts().mean() # counts rows for each category and calculate mean
df['category_col'].value_counts().idxmax() #most frequently appearing value
df.groupby('group_col')['value'].nunique() # count number of unique values for each group
df1.equals(df2) # if 2 datafrme is identical or not
df.isna().sum() # find na in a dataframe by column
df = df.sort_values(by='col1') # sorting 
df["A"] = df["A"].astype("category")
df.to_csv('output.txt', sep='\t', index=False, header=True)
# make dataframe
df = [['A', 1, 200],
     ['B', 2, 200]
     ]
column_names = ['Area', 'Ping', 'Frequency']
df = pd.DataFrame(df, columns=column_names)
# make dataframe from list
df = pd.DataFrame(my_list, columns=['Fruit'])
df = pd.DataFrame(list(zip(listA, liatB)), columns = ["col1", "col2"])
# make dataframe from series
df = pd.DataFrame(my_series)
# subsetting
df = df[(df['col1'] == 'group1')
    & (df['col2'] == 'A')
    & (df['col3'] > 10)
    ]
df.groupby('Group').first().reset_index() # get only first row 

# merge dataframe
merged_df = df.merge(temp_df, on=['pings.number', 'range'], how='left')
merged_df = pd.merge_asof(left=df, right=temp_df, on = 'DateTime', direction='nearest')
# add new column with condtion
df['C'] = np.where(df['A'] > 2, 'High A', 'Low A')
combined_df = pd.concat([df1, df2], ignore_index=True) # rbind
combined_df = pd.concat([df1, df2], axis=1) #cbind
text.split('_')[0] # extract before "_" from text="abc_def", so return "abc"


df['column'].unique() # get unique values in the column
df['column'].iloc[0] # get first item in 'range'
df['column'].describe() #summary of the column: min, max, mean
df.iloc[10] # show 10th row 
df['column'].value_counts()
df.groupby('Group2').size() # number of rows per group
df[df['column'] == 21720] # row in a dataframe which meat "column" == 21720
df.loc[(df['column1'] == 21720) & (df['column2'] == 199.5), 'column3'].values[0] # show precise value of column3 that meat 2 conditions on column1 and column2
del df # remove dataframe
df['DateTime'].str.len() # count number of letters
pd.Series(my_list) # convert list to pandas series
df['column'].tolist() # convert pandas series to list




# mean, max, min
# top largest values 
df[df['year'] == 2020].nlargest(10, 'TSC')
# group by mean
df.groupby(['Platform'])['vessel_speed'].mean()
summary_df = df.groupby(['Group', 'Area']).agg(
    total_colA=('colA', 'sum'),
    avg_colA=('colA', 'mean'),
    max_colB=('colB', 'max'),
    count_colC=('colC', 'count')
).reset_index()


# zip file
zip_file_path = 'my_archive.zip'
file_in_zip = 'temp_data.csv'
with zipfile.ZipFile(zip_file_path, 'r') as zf:
    with zf.open(file_in_zip) as file_obj:
        df = pd.read_csv(file_obj)




    
# dictionary
list(my_dict.values())[0] # take first value
list(my_dict.keys())[0] #take first key
my_dict = {
    'Key1': [[-3.25, -0.6, 5.918, -44.55]],
    'Key2': [[-3.28, -1.3, 5.93, -47.67], [1.76, 1.95, 8.889, -51.74]],
    'Key3': [[-3.46, -1.82, 5.936, -50.15], [-0.03, -1.41, 10.041, -46.98]],
}
df = pd.DataFrame.from_dict(my_dict, orient = 'index') # convert dictionary to dataframe #orient = 'columns' 



# Set options to display all rows and columns
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
# reset
pd.reset_option('display.max_rows')
pd.reset_option('display.max_columns')
pd.reset_option('display.max_colwidth')



# simple plot
%matplotlib qt
plt.plot(df['Frequency'], df['r(200)']) 
plt.scatter(df['Depth'], df['Depth_sum_NASC'])
plt.plot(df[(df['pings.number'] == 5574)]['Frequency'], df[(df['pings.number'] == 5574)]['r(200)'])
plt.hist(df[(df['pings.number']==5574)]['tsc'], bins=30)
# scatterplot by group
plot_df['Group_numeric'] = pd.factorize(plot_df['Group'])[0]
plt.scatter(plot_df['Depth'], plot_df['Depth_sum_NASC'], c = plot_df['Group_numeric'], cmap = 'viridis', marker = 'o', ms = 0.5)
# color map1
unique_experiments = sorted(final_result['experiment_no'].dropna().unique())
colors = plt.cm.viridis(np.linspace(start=0, stop=1, num=8))
color_map = {exp_num: colors[i] for i, exp_num in enumerate(unique_experiments)}
# color map2 (use import seaborn as sns)
unique_experiments = sorted(final_result['experiment_no'].dropna().unique())
set2_colors = sns.color_palette("Set2", 8)
color_map = dict(zip(unique_experiments, set2_colors[:len(unique_experiments)]))
# seaborn package
sns.boxplot(x= 'Platform', y='area_under_curve', data = plot_df)


# console
%qtconsole
%history -g bbts # search all code with "bbts" in history

# function run
%run -i Functions.ipynb

# System (in commandpromt)
pip list -v #chack all packages 
numpy.__version__ #check library version you use, need to be imported first
pip show numpy #check the version
pip index versions numpy # show available versions
pip install --force-reinstall numpy==1.26.4 # forcefully install specific version of the package (i.e. numpy )

dir(numpy) #show all modules
dir(numpy.linalg) # show submodules
type(obj) # check class of object




#statistics
import statsmodels.formula.api as smf
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import statsmodels.api as sm
from scipy import stats

# Student's t-test (Assuming equal variance)
t_statistic, p_value = stats.ttest_ind(sV_when_moving, sV_when_slow, equal_var=True, nan_policy='omit')
print(f"Independent T-test (equal variance): t-statistic = {t_statistic:.3f}, p-value = {p_value:.3f}")
print(f"n of moving= {np.sum(~np.isnan(sV_when_moving))}, n of slow to stop= {np.sum(~np.isnan(sV_when_slow))} ")

# Linear mixed model
filtered_df['Group'] = filtered_df['Area'].astype(str) + "_"  + filtered_df['year'].astype(str) #filtered_df['Day.Night'].astype(str) + "_" +
model = smf.mixedlm("log_PSU_mean_NASC ~ Platform", filtered_df, groups=filtered_df["Group"]).fit()
print(model.summary())
#tukey_results = pairwise_tukeyhsd(endog = model.resid, groups=filtered_df['Platform'], alpha=0.05)
tukey_results = pairwise_tukeyhsd(endog=filtered_df['log_PSU_mean_NASC'], groups=filtered_df['Platform'], alpha=0.05)
print(tukey_results)

# one-way ANOVA (https://www.kaggle.com/code/haseebwar07/hypothesis-testing-and-anova-post-hoc-with-python)
ols_formula = 'log_PSU_mean_NASC ~ C(Platform)'
model = smf.ols(formula = ols_formula, data = filtered_df[filtered_df['year']== 2024]).fit()
print(model.summary())
print(sm.stats.anova_lm(model, typ=2)) # determine whether there is a significant difference in NASC among groups
tukey_oneway = pairwise_tukeyhsd(endog = filtered_df[filtered_df['year']== 2024]["log_PSU_mean_NASC"], groups = filtered_df[filtered_df['year']== 2024]["Platform"])
print(tukey_oneway.summary())
