'''
This script performs a word search on words related to (as defined by cosine similarities of word embeddings) a given search term on a given artist's songs.
The output of the search can be found as a txt file in the 'out' folder.
'''

# import modules
import gensim
import gensim.downloader as api
import os
import pandas as pd
import string
import re
import argparse 
import sys

# define argument parser
def argument_parser():

    parser = argparse.ArgumentParser()

    parser.add_argument('--artist', type=str, help= 'Name of artist to search for in query', default='ABBA')
    parser.add_argument('--search_term', type=str, help= 'name of keyword to search for', default='love')

    args = vars(parser.parse_args())
    
    return args

# define preprocessing function
def preprocess(text_column): 

    '''
    Function to preprocess a column of text.

    Arguments:
    - text_column: column or list containing strings to preprocess.

    Returns:
        List of cleaned and preprocessed texts
    '''

    # initialize empty list
    cleaned_texts = []

    # loop over each text in the dataframe column containg lyrics
    for song in text_column:

        # convert to lowercase
        text_lower = song.lower()

        # remove line breaks
        preprocessed_text = text_lower.replace("\n", "")

        # remove punctuations, commas, etc. (; , . : ')
        cleaned_text = re.sub(r'[^\w\s]', '', preprocessed_text)

        cleaned_texts.append(cleaned_text)
    
    return cleaned_texts

def filter_and_clean(df, artist):

    '''
    Function that takes a given dataframe, filters it based on a chosen artist and preprocesses it.

    Arguments:
    - df: Pandas dataframe containing songs by different artists (i.e., containing a column called 'artist')
    - artist: what artist to filter the dataframe by

    Returns:
    - Filtered and preprocessed pandas dataframe containing only songs by the chosen artist
    '''

    # create new df with only the chosen artist
    artist_df = df[(df['artist'] == artist)]

    # if chosen artist is not available in the data, exit the script
    if artist_df.empty:
        print(f'Error: Songs by {artist} are not available in this dataset. Try another one.')
        sys.exit()

    else:
        # preprocess using defined function
        cleaned_text = preprocess(artist_df['text'])

        # create new column with cleaned text
        artist_df['cleaned_text'] = cleaned_text

        return artist_df

def find_word_matches(song, similar_words):
    '''
    Find exact word matches from a list of similar words to a chosen search term.

    Arguments:
        - song: song to search for word matches in
        - similar_words: list of words to search for in the song
    
    Returns:
        A count of how many of the words are present in the song.
    '''

    # initialize empty word count variable
    word_count = 0

    # for each of the similar words
    for word in similar_words:

        # look for exact word match using regular expressions (i.e., if looking for 'love', 'loves' will not be a match)
        matches = re.findall(r'\b' + word + r'\b', song)

        # append number of matches to word count
        word_count += len(matches)
    
    return word_count

def calc_percentages(model, search_term, cleaned_text_column):

    '''
    Function to calculate how many percentage of songs contain words related to the search term.

    Arguments:
        - model: loaded model from gensim to use for word embeddings
        - search_term: search word to find similar words to
        - cleaned_text_column: column in a pandas dataframe containing preprocessed text to apply word search to

    Returns:
        Percentage (as decimal number) of songs containing words related to the chosen search term

    '''
    # find the 10 most similar words to the search term
    try:
        similar_words = model.most_similar(search_term, topn=10)
    
    # if the search term is not available in the chosen model's vocabulary, exit the script
    except:
        print("Error: Search term is not available in the chosen model. Try another one.")
        sys.exit()

    # save only the words, not cosine similarities, of the similar words
    similar_words_tolist = [word[0] for word in similar_words]

    # add the search term to the list of words to search for
    similar_words_tolist.append(search_term)
    
    # initialize empty variable counting amount of texts containing similar words
    texts_w_words = 0

    # loop over each song in the text column
    for song in cleaned_text_column:

        # find matches for the similar words
        count = find_word_matches(song, similar_words_tolist)

        # if there is at least one of the words in the song, add to count variable
        if count > 0:
            texts_w_words += 1
    
        else:
            continue
    
    # calculate percentage of songs containing the query search words
    percentage = texts_w_words / len(text_column)

    return percentage

def save_result(percentage, artist, search_term):

    '''
    Save results from expanded word query to a txt file in the 'out' folder.

    Arguments:
        - percentage: amount of songs containing words related to the search word
        - artist: artist that has been used for the search
        - search_term: original search term that has been searched for
    
    Returns:
        None
    '''

    # round decimal number and convert to percentage
    percentage_calc = round(percentage, 2) * 100

    # create result string
    result = f"{percentage_calc}% of {artist}'s songs contain words related to '{search_term}'"

    # create outfile name
    outfile_name = f"{artist}_{search_term}.txt"

    # define out path
    out_path = os.path.join("out", outfile_name)

    # save txt with results in the out folder
    with open(out_path, 'w') as file:
                file.write(result)

def query_search(df, artist, model, search_term):

    '''
    Perform expanded query search on a given artist and search term.
    Results are saved in the 'out' folder.

    Arguments:
        - df: pandas df containing song lyrics data with 'artist' and 'text' columns
        - artist: chosen artist
        - model: gensim model to use for word embeddings
        - search_term: chosen search term to find similar words to and search for in songs
    
    Returns
        None
    '''

    # create df with only the searched for artist
    artist_df = filter_and_clean(df, artist)

    # find percentage of songs containing words similar to or the search term
    result = calc_percentages(model, search_term, artist_df['cleaned_text'])

    # save txt file with result
    save_result(result, artist, search_term)

def main():

    # load args
    args = argument_parser()
    
    # load glove model from gensim
    model = api.load("glove-wiki-gigaword-50")

    # define path to Spotify data and load to pandas df
    in_path = os.path.join('in', 'Spotify Million Song Dataset_exported.csv')
    df = pd.read_csv(in_path)

    # perform expanded query search on the desired artist and search term
    query_search(df, args['artist'], model, args['search_term'])

if __name__ == '__main__':
   main()

