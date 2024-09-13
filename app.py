import streamlit as st
import pandas as pd
import pickle
import requests

# Add custom CSS for improved design
page_bg_style = '''
<style>
.stApp {
    background-color: #f0f2f6;  /* Light gray background */
    color: #333333;  /* Dark gray text for better readability */
}

.stSelectbox, .stButton {
    background-color: #e0f7fa !important;  /* Light blue color for selection box */
    color: #01579b !important;  /* Dark blue text */
    font-size: 14px !important;  /* Adjusted font size */
    padding: 8px !important;  /* Added padding */
    width: 50% !important;  /* Reduced width for a clean look */
    margin: auto !important;  /* Center the selection box */
    border-radius: 5px;  /* Rounded corners */
}

.stButton button {
    background-color: #039be5 !important;  /* Subtle blue for the button */
    color: white !important;
    border: none !important;
    border-radius: 5px;
    padding: 10px 20px;
    font-size: 16px;
    margin-top: 20px;
    cursor: pointer;
    transition: background-color 0.3s ease-in-out;
}

.stButton button:hover {
    background-color: #0277bd !important;  /* Darker blue on hover */
}

h1, h2, h3, h4, h5, h6 {
    color: #01579b;  /* Dark blue headers for a professional look */
    text-align: center;  /* Center the header text */
}

</style>
'''

# Inject the CSS into the Streamlit app
st.markdown(page_bg_style, unsafe_allow_html=True)

# Paths for the model files
movie_list_path = 'C:/Users/merlin.f_servify/moviereconnedersystem/pythonProject2/model/movie_list.pkl'
similarity_path = 'C:/Users/merlin.f_servify/moviereconnedersystem/pythonProject2/model/similarity.pkl'

# TMDb API key
TMDB_API_KEY = '67e379f1ef439bb166653dee0c11f0d1'


# Function to fetch the poster and additional details from TMDb
def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    try:
        # Disable SSL verification
        response = requests.get(url, verify=False)
        data = response.json()

        if 'poster_path' in data and data['poster_path']:
            poster_path = data['poster_path']
            poster_url = f"https://image.tmdb.org/t/p/w300/{poster_path}"  # Smaller poster
        else:
            poster_url = 'https://via.placeholder.com/300x450?text=No+Poster+Available'

        rating = data.get('vote_average', 'N/A')

        return poster_url, rating
    except Exception as e:
        st.error(f"Error fetching movie details: {e}")
        return 'https://via.placeholder.com/300x450?text=Error+Fetching+Poster', 'N/A'


# Function to recommend movies
def recommend(movie):
    try:
        index = movies[movies['title'] == movie].index[0]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

        recommended_movie_names = []
        recommended_movie_posters = []
        recommended_movie_ratings = []
        recommended_movie_links = []

        for i in distances[1:6]:  # Get top 5 recommendations
            movie_id = movies.iloc[i[0]].movie_id
            poster, rating = fetch_movie_details(movie_id)
            recommended_movie_posters.append(poster)
            recommended_movie_names.append(movies.iloc[i[0]].title)
            recommended_movie_ratings.append(rating)
            recommended_movie_links.append(f"https://www.themoviedb.org/movie/{movie_id}")

        return recommended_movie_names, recommended_movie_posters, recommended_movie_ratings, recommended_movie_links
    except Exception as e:
        st.error(f"Error during recommendation: {e}")
        return [], [], [], []


# Streamlit UI
st.header('Movie Recommender System')

# Loading pickle files
try:
    with open(movie_list_path, 'rb') as f:
        movies = pickle.load(f)
    with open(similarity_path, 'rb') as f:
        similarity = pickle.load(f)
except FileNotFoundError as e:
    st.error(f"File not found: {e.filename}")
    st.stop()
except Exception as e:
    st.error(f"An error occurred while loading data: {e}")
    st.stop()

# Display movie selection dropdown
movie_list = movies['title'].values
selected_movie = st.selectbox("Type or select a movie from the dropdown", movie_list)

# Show details of the selected movie
if selected_movie:
    poster_url, rating = fetch_movie_details(movies[movies['title'] == selected_movie].movie_id.values[0])

    # Display selected movie details
    st.write("### Selected Movie")
    cols = st.columns([1, 2])  # Create two columns
    with cols[0]:
        st.image(poster_url, use_column_width='auto')  # Smaller poster
    with cols[1]:
        st.write(f"**Title:** {selected_movie}")
        st.write(f"**Rating:** {rating}")

# Show recommendations
if st.button('Show Recommendation'):
    recommended_movie_names, recommended_movie_posters, recommended_movie_ratings, recommended_movie_links = recommend(
        selected_movie)

    # Display the recommendations in columns
    st.write("### Recommendations")
    cols = st.columns(5)
    for idx, col in enumerate(cols):
        if idx < len(recommended_movie_names):
            with col:
                st.text(recommended_movie_names[idx])
                st.text(f"Rating: {recommended_movie_ratings[idx]}")
                if recommended_movie_links[idx]:
                    st.markdown(f"[![Poster]({recommended_movie_posters[idx]})]({recommended_movie_links[idx]})",
                                unsafe_allow_html=True)
                else:
                    st.image(recommended_movie_posters[idx])
