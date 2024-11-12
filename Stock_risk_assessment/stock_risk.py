import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import time
import os
from tqdm import tqdm
 
# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')
 
# -------------------------------
# 1. Load Stock Tickers from CSV
# -------------------------------
 
def load_stock_tickers(csv_path):
    """
    Load stock tickers from a CSV file.
 
    Parameters:
        csv_path (str): Path to the CSV file containing stock tickers.
 
    Returns:
        list: List of stock tickers.
    """
    try:
        df = pd.read_csv(csv_path)
        # Ensure the 'SYMBOL' column exists
        if 'SYMBOL' not in df.columns:
            raise ValueError("CSV file must contain a 'SYMBOL' column.")
        
        # Extract all unique symbols
        tickers = df['SYMBOL'].dropna().unique().tolist()
        print(f"Loaded {len(tickers)} tickers from '{csv_path}'.")
        return tickers
    except FileNotFoundError:
        print(f"Error: The file '{csv_path}' does not exist.")
        return []
    except Exception as e:
        print(f"Error loading tickers: {e}")
        return []
 
# ----------------------------------------
# 2. Fetch Stock Data in Batches
# ----------------------------------------
 
def fetch_and_save_stock_data(tickers, batch_size=200, start_date='2023-05-01', end_date='2024-11-09', output_csv='sample_indian_stocks_data_full.csv'):
    """
    Fetch stock data in batches and append to a CSV file.
 
    Parameters:
        tickers (list): List of stock tickers.
        batch_size (int): Number of tickers to process in each batch.
        start_date (str): Start date for historical data (YYYY-MM-DD).
        end_date (str): End date for historical data (YYYY-MM-DD).
        output_csv (str): Path to the output CSV file.
    """
    # Initialize the CSV file with headers if it doesn't exist
    if not os.path.exists(output_csv):
        headers = ['Ticker', 'Sector', 'Market Cap', 'P/E Ratio', 'Average Return', 'Volatility']
        with open(output_csv, 'w') as f:
            f.write(','.join(headers) + '\n')
        print(f"Created '{output_csv}' with headers.")
    else:
        print(f"Appending to existing '{output_csv}'.")
 
    total_tickers = len(tickers)
    total_batches = int(np.ceil(total_tickers / batch_size))
    
    print(f"\nFetching data in {total_batches} batches of {batch_size} tickers each...\n")
    
    for i in tqdm(range(0, total_tickers, batch_size), desc="Processing Batches"):
        batch_tickers = tickers[i:i + batch_size]
        try:
            # Fetch historical price data for the batch
            for ticker in batch_tickers:
                try:
                    print(f"Processing {ticker}...")
                    stock = yf.Ticker(ticker)
                    
                    # Fetch historical price data
                    hist = stock.history(start=start_date, end=end_date)
                    if hist.empty:
                        print(f"No historical data found for {ticker}. Skipping.")
                        continue
                    
                    # Calculate daily returns
                    hist['Daily Return'] = hist['Close'].pct_change()
                    avg_return = hist['Daily Return'].mean()
                    volatility = hist['Daily Return'].std()
                    
                    # Fetch financial info
                    info = stock.info
                    sector = info.get('sector', 'Unknown')
                    market_cap = info.get('marketCap', np.nan)
                    pe_ratio = info.get('trailingPE', np.nan)
                    
                    # Prepare row data
                    row = {
                        'Ticker': ticker,
                        'Sector': sector,
                        'Market Cap': market_cap if not pd.isna(market_cap) else '',
                        'P/E Ratio': pe_ratio if not pd.isna(pe_ratio) else '',
                        'Average Return': avg_return,
                        'Volatility': volatility
                    }
                    
                    # Append to CSV
                    with open(output_csv, 'a') as f:
                        f.write(f"{row['Ticker']},{row['Sector']},{row['Market Cap']},{row['P/E Ratio']},{row['Average Return']},{row['Volatility']}\n")
                    
                    print(f"Data fetched and saved for {ticker}.\n")
                    
                    # Optional: Sleep to respect API rate limits
                    time.sleep(0.1)
                
                except Exception as e:
                    print(f"Error processing {ticker}: {e}\n")
                    continue
            
            # Optional: Sleep between batches
            time.sleep(1)
        
        except Exception as e:
            print(f"Error fetching batch starting at index {i}: {e}")
            continue
    
    print(f"\nData fetching completed. Consolidated data saved to '{output_csv}'.")
 
# ----------------------------------------
# 3. Preprocess the Consolidated Data
# ----------------------------------------
 
def preprocess_data(input_csv='sample_indian_stocks_data.csv'):
    print("\nPreprocessing data...")
 
    # Load the consolidated CSV
    df = pd.read_csv(input_csv)
    print(f"Loading the latest diversification metrics...")
 
    # 3.1 Handle Missing Values
    essential_columns = ['Sector', 'Market Cap', 'P/E Ratio', 'Average Return', 'Volatility']
    df_clean = df.dropna(subset=essential_columns).reset_index(drop=True)
 
    # 3.2 Encode Categorical Variables (Sector) using pd.get_dummies
    sector_encoded_df = pd.get_dummies(df_clean['Sector'], prefix='Sector')
 
    # 3.3 Concatenate Encoded Columns with Main DataFrame
    df_final = pd.concat([df_clean.drop('Sector', axis=1), sector_encoded_df], axis=1)
 
    # 3.4 Handle any potential NaN or infinite values in the numerical columns
    numerical_features = ['Market Cap', 'P/E Ratio', 'Average Return', 'Volatility']
    
    # Replace infinities with NaN, then drop rows with NaN in these columns
    df_final[numerical_features] = df_final[numerical_features].replace([np.inf, -np.inf], np.nan)
 
    # Drop rows where any of the numerical features have NaN values
    df_final = df_final.dropna(subset=numerical_features)
 
    # 3.5 Feature Scaling
    scaler = StandardScaler()
    df_final[numerical_features] = scaler.fit_transform(df_final[numerical_features])
 
    print("Preprocessing completed.")
    return df_final
 
# ----------------------------------------
# 4. Determine Optimal Number of Clusters
# ----------------------------------------
 
def determine_optimal_clusters(X, max_k=10):
    """
    Determine the optimal number of clusters using Elbow Method and Silhouette Score.
 
    Parameters:
        X (pd.DataFrame or np.ndarray): Feature matrix.
        max_k (int): Maximum number of clusters to try.
 
    Returns:
        int: Optimal number of clusters.
    """
    # print("\nDetermining the optimal number of clusters...")
    wcss = []
    silhouette_scores = []
    K = range(2, max_k+1)
 
    for k in K:
        kmeans = KMeans(n_clusters=k, init='k-means++', random_state=42)
        labels = kmeans.fit_predict(X)
        wcss.append(kmeans.inertia_)
        score = silhouette_score(X, labels)
        silhouette_scores.append(score)
        # print(f"K={k}: WCSS={kmeans.inertia_:.2f}, Silhouette Score={score:.4f}")
 
    # Plot Elbow Method
    # plt.figure(figsize=(14, 6))
 
    # plt.subplot(1, 2, 1)
    # plt.plot(K, wcss, 'bo-', markersize=8)
    # plt.xlabel('Number of Clusters (K)')
    # plt.ylabel('WCSS')
    # plt.title('Elbow Method For Optimal K')
    # plt.xticks(K)
 
    # # Plot Silhouette Scores
    # plt.subplot(1, 2, 2)
    # plt.plot(K, silhouette_scores, 'bo-', markersize=8)
    # plt.xlabel('Number of Clusters (K)')
    # plt.ylabel('Silhouette Score')
    # plt.title('Silhouette Scores For Various K')
    # plt.xticks(K)
 
    # plt.tight_layout()
    # plt.show()
 
    # Choose the K with the highest Silhouette Score
    optimal_k = 8
    # print(f"\nOptimal number of clusters determined to be: {optimal_k}")
    return optimal_k
 
# ----------------------------------------
# 5. Perform Clustering
# ----------------------------------------
 
def perform_clustering(X, n_clusters):
    """
    Perform K-Means clustering.
 
    Parameters:
        X (pd.DataFrame or np.ndarray): Feature matrix.
        n_clusters (int): Number of clusters.
 
    Returns:
        KMeans: Fitted KMeans object.
        np.ndarray: Cluster labels.
    """
    # print(f"\nPerforming K-Means clustering with K={n_clusters}...")
    kmeans = KMeans(n_clusters=n_clusters, init='k-means++', random_state=42)
    labels = kmeans.fit_predict(X)
    # print("Clustering completed.")
    return kmeans, labels
 
# ----------------------------------------
# 6. Save Clustering Results
# ----------------------------------------
 
def save_clustering_results(df, labels, output_path='indian_stocks_clusters.csv'):
    """
    Save the clustering results to a CSV file.
 
    Parameters:
        df (pd.DataFrame): Preprocessed stock data.
        labels (np.ndarray): Cluster labels.
        output_path (str): Path to save the CSV file.
    """
    df_with_clusters = df.copy()
    df_with_clusters['Cluster'] = labels
    df_with_clusters.to_csv(output_path, index=False)
    # print(f"\nClustering results saved to '{output_path}'.")
 
# ----------------------------------------
# 7. Analyze User Portfolio and Recommend Stocks
# ----------------------------------------
 
def analyze_user_portfolio(clustered_df, user_portfolio, top_n=5):
    """
    Analyze the user's portfolio clusters and recommend stocks from other clusters.
 
    Parameters:
        clustered_df (pd.DataFrame): DataFrame with clustering results.
        user_portfolio (list): List of user's stock tickers.
        top_n (int): Number of stock recommendations.
 
    Returns:
        pd.DataFrame: Recommended stocks.
    """
    print("\nAnalyzing user portfolio...")
 
    # Filter user's stocks
    user_stocks = clustered_df[clustered_df['Ticker'].isin(user_portfolio)]
 
    if user_stocks.empty:
        print("No matching stocks found in the clustering results for the user portfolio.")
        return pd.DataFrame()
 
    # Display user's stocks and their clusters
    # saving user_stocks[['Ticker', 'Cluster']] to a csv file
    user_stocks[['Ticker', 'Cluster']].to_csv('user_portfolio_clusters.csv', index=False)
 
    # Identify clusters present in user's portfolio
    user_clusters = user_stocks['Cluster'].unique()
 
    # Filter stocks not in user's clusters
    recommended_stocks = clustered_df[~clustered_df['Cluster'].isin(user_clusters)]
 
    if recommended_stocks.empty:
        print("No clusters available for recommendations outside the user's current clusters.")
        return pd.DataFrame()
 
    # Sort the recommended stocks by Average Return in descending order
    recommended_stocks_sorted = recommended_stocks.sort_values(by='Average Return', ascending=False)
 
    # Recommend top N stocks from other clusters
    top_recommendations = recommended_stocks_sorted.head(top_n)
 
    print(f"\nTop {top_n} Recommended Stocks from Other Clusters:")
    print(top_recommendations[['Ticker', 'Cluster', 'Average Return']])
 
    return top_recommendations[['Ticker', 'Cluster', 'Average Return']]
 
# ----------------------------------------
# 8. Visualize Clusters using PCA
# ----------------------------------------
 
def plot_clusters(df, n_clusters):
    """
    Visualize clusters using PCA for dimensionality reduction.
 
    Parameters:
        df (pd.DataFrame): Preprocessed data with cluster labels.
        n_clusters (int): Number of clusters.
    """
    from sklearn.decomposition import PCA
 
    # Separate features and cluster labels
    X = df.drop(['Ticker', 'Cluster'], axis=1)
    labels = df['Cluster']
 
    # Apply PCA to reduce to 2 dimensions for visualization
    pca = PCA(n_components=2, random_state=42)
    principal_components = pca.fit_transform(X)
 
    # Create a DataFrame with principal components and cluster labels
    pca_df = pd.DataFrame(data=principal_components, columns=['PC1', 'PC2'])
    pca_df['Cluster'] = labels
 
# ----------------------------------------
# 9. Main Execution Flow
# ----------------------------------------
 
def main(sample_user_portfolio):
    # Define the path to your CSV file containing all stock tickers
    # Since your data is already in 'sample_indian_stocks_data.csv', we skip fetching
    input_csv = 'updated_sample_indian_stocks_data.csv'
    
    if not os.path.exists(input_csv):
        print(f"CSV file not found at '{input_csv}'. Please check the path and try again.")
        return
 
    # Step 1: Preprocess the consolidated data
    df_preprocessed = preprocess_data(input_csv=input_csv)
    if df_preprocessed.empty:
        # print("Preprocessed data is empty. Exiting.")
        return
 
    # Step 2: Determine the optimal number of clusters
    X = df_preprocessed.drop(['Ticker'], axis=1)
    optimal_k = determine_optimal_clusters(X, max_k=10)
 
    # Step 3: Perform clustering
    kmeans, labels = perform_clustering(X, optimal_k)
 
    # Step 4: Save clustering results
    save_clustering_results(df_preprocessed, labels, output_path='indian_stocks_clusters.csv')
 
    # Step 5: Analyze user portfolio and recommend stocks
    # Define a sample user portfolio
    # Modify this list with actual ticker symbols present in your dataset
 
    # Load the clustering results
    clustered_df = pd.read_csv('indian_stocks_clusters.csv')
 
    # Analyze and get recommendations
    recommendations = analyze_user_portfolio(clustered_df, sample_user_portfolio, top_n=5)
 
    # Optional: Save recommendations to a CSV file
    if not recommendations.empty:
        recommendations.to_csv('recommended_stocks.csv', index=False)
        # print("\nRecommended stocks saved to 'recommended_stocks.csv'.")
 
    # Optional: Visualize clusters using PCA
    visualize_clusters = True
    if visualize_clusters:
        plot_clusters(clustered_df, optimal_k)
        
if __name__ == "__main__":
    df = pd.read_excel('user_data.xlsx')
    tickers = df['Stock Ticker'].tolist()
    sample_user_portfolio = tickers
    main(sample_user_portfolio)
