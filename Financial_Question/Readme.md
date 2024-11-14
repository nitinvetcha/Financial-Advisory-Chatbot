"""This code is by Nitin Vetcha"""

Description:
------------
This script is designed to assess the risk tolerance level of the user based on his personal information which includes details pertaining but not limited to marital status, current employment status, primary financial goals, gender, age, current life stage, home ownership status, previous investment experience, stock volatility preference, investment horizon, market reaction, number of dependents, monthly income, liability, total asset value, fixed asset value and expected return percentage.

User would be permitted to submit subjective answers for each of the questions : "What is your marital status?", "Are you currently employed?",  "What are your primary financial goals?", "What is your gender?", "How would you describe your current life stage?", "What is your home ownership status?", "What is your investment experience?", "What would you do if your investment lost 20 percent in a year?", "What level of volatility would you be most comfortable with?", "How long do you plan to hold your investments?", "What's your risk capacity (ability to take risks)?", "How old are you?", "How many dependents do you have?", "What is your monthly income?", "How much liability do you have?", "What is the estimated value of all your assets?", "What is the estimated value of your fixed assets?", "What percentage of the investment do you expect as monthly return?". Each question has a set of associated classes with as well such ("Single", "Common law", "Married", "Separated", "Divorced", "Widowed") for marital status, ("Retirement", "Home purchase", "Education", "Emergency fund", "Wealth accumulation") for primary financial goals, ("Starting out", "Career building", "Peak earning years", "Pre-retirement", "Retirement") for current life stage etc.

I then used facebook/bart-large-mnli model, which can be accessed from Hugging face using an API key. This would act on the text corpus obtained from the user, and perform a classification task for each question. It outputs the probability (confidence level) for each class as well. Now, each class has an associated score indicating its contribution to the final risk evaluation, calculated as prescribed in the GitHub repository cited in the references. However, they consider only a discrete version, which I improvised by taking into account the uncertainity associated with each class as well while computing the score. The output is finally the computed risk score for eaach question normalized to ensure it lies between 0 and 1, presented as a tabular data for user reference and further usage as well. If the user intends to share his personal information, this risk value would be as the preferred risk tolerance level in the portfolio optimzation module, else a default value would be used. To respect user privacy, this module has been kept optional, implying the user can skip if he / she doesnt feel comfortable in providing the requisite information. 

Motivation:
-----------
The primary motivation to implement this module stems for the notable highly cited paper - Financial risk tolerance: An analysis of unexplored factors
- published in the prestigious Financial Review Service journal in 2013. Based on the study perfomered, it was noted that there exists a positive correlation between risk  tolerance and income, investment knowledge and positive stock market expectations.

Input:
------------
The list of stocks is provided via a CSV file, which includes most of the indian stocks available on yfinance.(around 1200 stocks are there in the csv will be there in the references section.) 
This file includes various stock metrics like Market Cap, P/E Ratio, Average Return, Volatility, and Sector information. 
The dataset has been preprocessed with one-hot encoding for certain categorical features, gathered through API calls to yFinance (handled in batches due to API call limits).

Overview of the Code:
---------------------
The script is structured into the following main components:

1. **Sentiment Analysis Function:** Uses a BERT model to predict the sentiment of given text (Reddit posts and YouTube comments).
2. **Reddit Sentiment Analysis:** Fetches recent Reddit posts related to the stock and analyzes their sentiment.
3. **YouTube Sentiment Analysis:** (Optional) Fetches YouTube comments related to the stock and analyzes their sentiment.
4. **Risk Score Calculation:** Combines the beta value from yFinance and the adjusted sentiment score to compute the final risk score for the stock.

How to Use:
-----------
1. Replace the placeholders for Reddit API credentials and YouTube API key with your own credentials.
2. Run the script to calculate risk scores for individual stocks or an entire list from a CSV file.

References:
-----------
1. https://github.com/m-turnergane/investment-risk-assessor
2. https://opus.lib.uts.edu.au/handle/10453/23532
