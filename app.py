from flask import Flask,render_template,request
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
# popular_df = pickle.load(open('popular.pkl','rb'))
# pt = pickle.load(open('pt.pkl','rb'))
# books = pickle.load(open('books.pkl','rb'))
# similarity_scores = pickle.load(open('similarity_scores.pkl','rb'))

books_by_P = pd.read_pickle('popular.pkl')
pt = pd.read_pickle('pt.pkl')
books = pd.read_pickle('books.pkl')
booksByUser = pd.read_pickle('booksByUser.pkl')
similarity_scores = pd.read_pickle('similarity_scores.pkl')

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html',
        book_name = list(books_by_P['Book-Title'].values),
        author=list(books_by_P['Book-Author'].values),
        image=list(books_by_P['Image-URL-M'].values),
    )

@app.route('/recommend-by-category')
def recommendCategoryPage():
    return render_template('recommend-by-category.html')

@app.route('/recommend-by-category',methods=['post'])
def recommendByCategory():
    user_input = request.form.get('user_input')
    if(user_input == '') :
        return render_template('recommend-by-category.html', success=False)
    index = np.where(pt.index == user_input)[0][0]
    similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[0:11]

    data = []
    for i in similar_items:
        item = []
        temp_df = books[books['Book-Title'] == pt.index[i[0]]]
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

        data.append(item)

    print(data)

    return render_template('recommend-by-category.html',data=data)

@app.route('/recommend-by-user')
def recommendUserPage():
    return render_template('recommend-by-user.html')

# defining a function to get similar users
def similar_users(user_index, interactions_matrix):
    similarity = []
    for user in range(0, interactions_matrix.shape[0]): #  .shape[0] gives number of rows
        
        #finding cosine similarity between the user_id and each user
        sim = cosine_similarity([interactions_matrix.loc[user_index]], [interactions_matrix.loc[user]])
        
        #Appending the user and the corresponding similarity score with user_id as a tuple
        similarity.append((user,sim))
        
    similarity.sort(key=lambda x: x[1], reverse=True)
    most_similar_users = [tup[0] for tup in similarity] #Extract the user from each tuple in the sorted list
    similarity_score = [tup[1] for tup in similarity] ##Extracting the similarity score from each tuple in the sorted list
   
    #Remove the original user and its similarity score and keep only other similar users 
    most_similar_users.remove(user_index)
    similarity_score.remove(similarity_score[0])
       
    return most_similar_users, similarity_score

# defining the recommendations function to get recommendations by using the similar users' preferences
def recommendationsBookByUser(user_index, num_of_products, interactions_matrix):
    
    #Saving similar users using the function similar_users defined above
    most_similar_users = similar_users(user_index, interactions_matrix)[0]
    
    #Finding product IDs with which the user_id has interacted
    prod_ids = set(list(interactions_matrix.columns[np.where(interactions_matrix.loc[user_index] > 0)]))
    recommendations = []
    
    observed_interactions = prod_ids.copy()
    for similar_user in most_similar_users:
        if len(recommendations) < num_of_products:
            
            #Finding 'n' products which have been rated by similar users but not by the user_id
            similar_user_prod_ids = set(list(interactions_matrix.columns[np.where(interactions_matrix.loc[similar_user] > 0)]))
            recommendations.extend(list(similar_user_prod_ids.difference(observed_interactions)))
            observed_interactions = observed_interactions.union(similar_user_prod_ids)
        else:
            break
    
    return recommendations[:num_of_products]

@app.route('/recommend-by-user',methods=['post'])
def recommendByUser():
    user_index = request.form.get('user_index')
    if(user_index == '') :
        return render_template('recommend-by-user.html', success=False)

    bookNames = recommendationsBookByUser(int(user_index), 12, booksByUser)
    data = []
    for i in bookNames:
        item = []
        temp_df = books[books['Book-Title'] == i]
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

        data.append(item)

    print(data)
    return render_template('recommend-by-user.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
