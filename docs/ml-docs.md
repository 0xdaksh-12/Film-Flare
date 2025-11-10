# Notes

## Non-Personalized Recommendation

### Finding the most liked items

Dataframe: User | Book | Rating

```python
user_rating[["book","rating"]].groupby(['book']).mean().sort_values(by="rating", ascending=False) # Book may review 1 or 2 time -> 5 Rating

# Filter low number of rating book
book_frequency = user_rating['book'].value_counts()
frequently_reviewed_book = book_frequency[book_frequency > 100].index

frequent_books_df=user_rating[user_rating_df['book'].isin(frequently_reviewed_book)]

frequent_books_df[["book","rating"]].groupby(['book']).mean().sort_values(by="rating", ascending=False)

```

## Non-Personalized Suggestions

### Identify pairs two books read together

Dataframe: UserId, books

```python

#  pairing function
from itertools import permutations

def create_pairs(x):
  pairs = pd.DataFrame(list(permutations(x.values, 2)), columns-['book_a', 'book_b'])
  return pairs

book_pairs = book_df.groupby('userId')['book_title'].apply(create_pairs).reset_index(drop=True)

book_pairs.groupby(['book_a', 'book_b']).size().to_frame(name = 'size').reset_index().sort_values('size', ascending=False)
```

## Content-Based

### Based on Similarity of item

```python
dataFrame -> title, genre

# Cross tab -> one to many RelationShip
               Row           Column
pd.crosstab(df['title'], df['genre'])

# Similarity between item
# Jaccard Similarity

from sklearn.metrics import jaccard_score

# One via One
hobbit_row = df.loc['The Hobbit']
GOT_row = df.loc('A Game of Thrones')
jaccard_score(hobbit_row, GOT_row) -> 0.5

# All item distance between
from scipy.spatical.distance import pdist, squareform

jaccard_distances = pdist(df.values, metric='jaccard')

square_jaccard_distances = squareform(jaccard_distances)

jaccard_similarity_array = 1 - square_jaccard_distances

# Creating a usable distance Table
new_df = pd.dataFrame(jaccard_similarity_array, index=df['title'], columns=df['book'])

# Find the most similar Book
new_df['The Hobbit'].sort_values(ascending=False)
```

### Text-based Similarities

```python

# Term Frequency inverse document Frequency

TF-IDF = ('Count of word occurrences')/('Total words in document') / (log('Number of docs word is in'/ 'Total number of docs'))

# Instantiate the vectorizer
from sklearn.feature_extraction.text import TfidfVectorizer

# Filter the data
tfidfvec = TfidfVectorizer(min_df=2, max_df=0.7)

# Vectorizing the data
vectorized_data = tfidfvec.fit_transform(df['Descriptions'])

tfidfvec.get_feature_names #-> Array of word
vectorized_data.to_array() #-> Array of Features


tfidf_df = pd.DataFrame(vectorized_data.to_array(), index=df['Book'], columns=tfidfvec.get_feature_names())

# Cosine Similarity -> Metric

# Cosine Distance  -> cos(0) = A.B / ||A||.||B||
# Measure the two angle between two documents

from sklearn.metrics.pairwise import cosine_similarity

# Find the similarity between all items
cosine_similarity_array = cosine_similarity(tfidf_df)

# Between two items
cosine_similarity(tfidf_df.loc['The Hobbit'].values.reshape(1, -1), tfidf_df.loc['Macbeth'].values.reshape(1, -1))
```

### User profile recommendations

```python
# Item to Item

list_of_books_read = ['The Hobbit', 'Foundation']
user_books = tfidf_df.reindex(list_of_books_read)

# Find recommendation for a user

# Create a subset of only the non-read books
non_user_books = tfidf_df.drop(list_of_books_read, axis=0)

# Calculate the consine similarity between all rows
user_prof_similarities = cosine_similarity(user_books.values.reshape(1, -1), non_user_books)

# Wrap in a DataFrame for ease of use
user_prof_similarities_df = pd.DataFrame(user_prof_similarities.T, index=tfidf_df.index, columns=['similarity_score']).sort_value(by="similarity_score", ascending=False)
```

## Collaborative Filtering
