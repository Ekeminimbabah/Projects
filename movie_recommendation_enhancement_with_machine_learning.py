# -*- coding: utf-8 -*-
"""Movie Recommendation Enhancement With Machine Learning

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1NMzCCV5t5SaCiWvGfYRKRiy_oDVuaZAA

## Data Preparaion ##
"""

import zipfile

zip_file_path = "/content/drive/MyDrive/movielens-20m-dataset.zip"

extract_dir = "/content/drive/MyDrive/movielens-20m-dataset"

with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
  zip_ref.extractall(extract_dir)

import pandas as pd

ratings = pd.read_csv("/content/drive/MyDrive/movielens-20m-dataset/rating.csv")

movies = pd.read_csv("/content/drive/MyDrive/movielens-20m-dataset/movie.csv")

"""## Carrying out EDA to understand the datasets ##"""

ratings.head()

ratings["rating"].unique()

ratings.shape

movies.head()

movies.shape

"""## Mergeing the movies table to the ratings table ##"""

df = pd.merge(movies, ratings, on="movieId", how="inner")

df.head()

df_values = df['title'].value_counts()

df_values.describe()

rare_movies = df_values[df_values < 10000].index

rare_movies

"""### Creating a table which contains movies that are watched more than 10000 times"""

df = df[~df['title'].isin(rare_movies)]

df.head()

df.shape

"""### Create a pivot table that contains ratings of movies watched more 10000 times"""

df = df.pivot_table(index="userId", columns="title", values="rating")

df

"""### We create an automated pipeline "function" that will automate this process if given dataset of this nature in the near future.

"""

def prepare_data_and_create_pivottable(df1, df2, min_vote=10000):
    # Make copies of the input DataFrames to avoid modifying the original data
    df1, df2 = df1.copy(), df2.copy()

    # Merge the movie table (df1) with the rating table (df2) on the "movieId" column using an inner join
    merge = pd.merge(df1, df2, on="movieId", how="inner")

    # Count the number of ratings for each movie title
    count = merge["title"].value_counts()

    # Identify rare movies that have fewer ratings than the specified minimum vote threshold
    rare_movies = count[count < min_vote].index

    # Filter out the rare movies from the merged DataFrame
    merge = merge[~merge["title"].isin(rare_movies)]

    # Create a pivot table with userId's as rows, movie titles as columns, and ratings as values
    df = merge.pivot_table(index="userId", columns="title", values="rating")

    return df

"""## User based Recommendation

#### Steps to follow
1. Select random user
2. Look at user Performance
3. Select other users eith similar viewing history(60%)
4. Rank the Users
5.Get their other rating and figure out which movie to recommend.
"""

#selecting random users
random_user = df.sample(1, random_state=37).index[0]

random_user

random_user_df = df[df.index == random_user] # Filter df for the random user

random_user_df

#Create a list of columns (movies) for which the random user has non-null entries
movies_watched = random_user_df.dropna(axis = 1).columns.tolist()

movies_watched

movie_watch_df = df[movies_watched]
movie_watch_df

movies_watched_df = df[movies_watched]
movies_watched_df

movies_watched_count = movies_watched_df.notnull().sum(axis=1)
movies_watched_count

movies_watched_count.max()

len(movies_watched)

# Create a list of movies watched by more than 60% of users
user_movies_watched = movies_watched_count[movies_watched_count > (movies_watched_df.shape[1]* 60) / 100].index

user_movies_watched

"""### We check the correlation between each users and the movies they have watched"""

# Filter the DataFrame to include only the rows (users) who have watched the movies in the user_movies_watched list
filtered_df = movies_watched_df[movies_watched_df.index.isin(user_movies_watched)]

filtered_df

corr_df = filtered_df.T.corr().unstack()

corr_df

"""### We want to compare how each user is correlated to our random user"""

corr_df[random_user]

top_user = pd.DataFrame(corr_df[random_user][corr_df[random_user] >0.65],columns=["movie_similarity"])

top_user

top_users_rating = pd.merge(top_user, ratings[["userId", "movieId", "rating"]],  how = "inner", on = "userId")

top_users_rating

top_users_rating['weihgted_rating'] = top_users_rating["rating"] * top_users_rating["movie_similarity"]

top_users_rating

recommendations_df = top_users_rating.pivot_table(values="weihgted_rating", index="movieId", aggfunc="mean")

recommendations_df

# Now use the correct column name in your filtering and sorting operations
movies_to_be_recommended = recommendations_df[recommendations_df["weihgted_rating"] > 3.5].sort_values(by = "weihgted_rating", ascending=False).head(10)

movies_to_be_recommended

"""### So we show the names of the top 10 recommended movies by our user-based filtering reccomender system."""

movies['title'][movies["movieId"].isin(movies_to_be_recommended.index)].head(10)

"""## Item based-recommender system

### Steps to take
"""

#1) User sample
sample_user = 49927
#2) The last heighest ranked movies our sample user watched
#3) Then try to see the content of the movies that could possibly make our user like the movie and what others
#say about the movie
#4) We get new movies from our movie dataset with similar content

pick = ratings[(ratings["rating"] == 5) & (ratings["userId"] == random_user)].sort_values(by="timestamp", ascending=False).iloc[1]["movieId"]

pick

picked_movie_name = movies["title"][movies["movieId"] == pick].iloc[0]

picked_movie_name

filtered_movie = movie_watch_df[picked_movie_name]

filtered_movie

users_without_user = df.drop(random_user, axis=0).drop(movies_watched, axis=1)

users_without_user

filtered_without_user = filtered_movie.drop(random_user, axis=0)

filtered_without_user

movies_similarities = users_without_user.corrwith(filtered_without_user).sort_values(ascending=False).reset_index()

movies_similarities.columns = ["title", "movie_similarity"]

content_similarity = movies_similarities.sort_values(by="movie_similarity", ascending=False).head(10)

"""### We show the top 10 movies recommended by our item-based recommender system"""

content_similarity

"""## Hybrid Recommender system"""

user_based_recommendation = movies['title'][movies["movieId"].isin(movies_to_be_recommended.index)]

"""### We display the top 10 movies recommended by our model using the user-based filtering recommender system."""

user_based_recommendation

recommendations_df

movie_ordeed_by_rating = pd.merge(recommendations_df, movies, on="movieId", how="inner")[["weihgted_rating", "title", "movieId"]]

movie_ordeed_by_rating

merge = pd.merge(content_similarity, movie_ordeed_by_rating, on="title", how="inner")

merge

merge["overall_rating"] = merge["movie_similarity"] * merge["weihgted_rating"]

merge

Final_recommendation = merge.sort_values(by="overall_rating", ascending=False).head(10)

"""## FINAL RECOMMENDATION

#### Our final reccomendation using the hybrid-filtering recommender system
"""

Final_recommendation["title"]

