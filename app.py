# import library
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask,render_template,request,jsonify
from mal import Anime
from mal import AnimeSearch
import pandas as pd
import requests
from bs4 import BeautifulSoup  
import pickle
import bz2
app = Flask(__name__)
#import csv 
df = pd.read_csv("reduced_anime_data.csv")
info_df = df
file = bz2.BZ2File('anime_similarity.bz2','rb')
similarity = pickle.load(file)
#######################$$$$$$$#############

@app.route("/")
def home():
    suggestions = get_suggestions()
    return render_template("home.html",suggestions =  suggestions)

def get_suggestions():
    data = pd.read_csv('titles.csv')
    return list(data['title'])

#this function fetch commnets from website
# in this function we use webscraping fot fetch commets and youtube link
def fetch_comment(uid):
    #use request library for fetch that website 
    req = requests.get("https://myanimelist.net/anime/{}".format(uid))

    # useing beautifulsoup for collect html data from website 
    soup = BeautifulSoup(req.content,"html.parser") 

    # now we fetch youtube link .fetch this class in website html and we convert to str 
    link = str(soup.find_all("a",class_="iframe js-fancybox-video video-unit promotion"))[64:151] 
    try:
        review1 = str(soup.find_all("br")[35])[0:300].replace("\r","").replace("<br>","").replace("\n","").replace("<br/>","").replace("<span id=review","")
        review2 = str(soup.find_all("br")[39])[0:300].replace("\r","").replace("<br>","").replace("\n","").replace("<br/>","").replace("<span id=review","")
        review3 = str(soup.find_all("br")[41])[0:300].replace("\r","").replace("<br>","").replace("\n","").replace("<br/>","").replace("<span id=review","")
        if "div" in review1 or "div" in review2 or "div" in review3:
                link = str(soup.find_all("a",class_="iframe js-fancybox-video video-unit promotion"))[64:151]
                review1 = str(soup.find_all("br")[45])[0:300].replace("\r","").replace("<br>","").replace("\n","").replace("<br/>","")
                review2 = str(soup.find_all("br")[46])[0:300].replace("\r","").replace("<br>","").replace("\n","").replace("<br/>","")
                review3 = str(soup.find_all("br")[47])[0:300].replace("\r","").replace("<br>","").replace("\n","").replace("<br/>","")
                return  review1,review2,review3,link
        elif "span" in review1 or "js-review-helpful" in review2 or "<span id=review" in review3:
                link = str(soup.find_all("a",class_="iframe js-fancybox-video video-unit promotion"))[64:151]
                review1 = str(soup.find_all("br")[48])[0:300].replace("\r","").replace("<br>","").replace("\n","").replace("<br/>","")
                review2 = str(soup.find_all("br")[49])[0:300].replace("\r","").replace("<br>","").replace("\n","").replace("<br/>","")
                review2 = str(soup.find_all("br")[50])[0:300].replace("\r","").replace("<br>","").replace("\n","").replace("<br/>","")
                return  review1,review2,review3,link
        else:
            return  review1,review2,review3,link
    except:
        link = str(soup.find_all("a",class_="iframe js-fancybox-video video-unit promotion"))[64:151]
        review1 = str(soup.find_all("br")[17])[0:300].replace("\r","").replace("<br>","").replace("\n","").replace("<br/>","")
        review2 = str(soup.find_all("br")[20])[0:300].replace("\r","").replace("<br>","").replace("\n","").replace("<br/>","")
        review3 = str(soup.find_all("br")[22])[0:300].replace("\r","").replace("<br>","").replace("\n","").replace("<br/>","")
        if "div" in  review1 or review2 or review3:
            s = "Sorry Comments is not available"
            return s , s, s ,link
        else:
            return  review1,review2,review3,link
def rec_name(mal_id):
    responese = requests.get("https://myanimelist.net/anime/{}".format(mal_id))
    sou = BeautifulSoup(responese.content,"html.parser")
    name = sou.find_all("span",class_="title fs10")
    p = pd.DataFrame(name)
    return p[0]
def only_anime(anime):
    search = AnimeSearch(anime)
    name = search.results[0].title
    img = search.results[0].image_url
    mal_id = search.results[0].mal_id
    uid = Anime(mal_id)
    genre = uid.genres
    aired = uid.aired
    score = search.results[0].score
    synopsis = search.results[0].synopsis
    
    return name,img,mal_id,genre,score,synopsis,aired

def fetch_poster(anime_name):
    if  info_df[info_df["title"]== anime_name].empty:
        search = AnimeSearch(anime_name)
        ida = search.results[0].image_url
        img_url1 = ida
        return img_url1
    else:
        index = info_df[info_df["title"]== anime_name].index[0]
        img_url = info_df.iloc[index,-4]
        return img_url

def main_info(name):
    index = info_df[info_df["title"]== name].index[0]
    uid = info_df.iloc[index,1]
    synopsis = info_df.iloc[index,3]
    score = info_df.iloc[index,-2]
    aired = info_df.iloc[index,-3]
    genre = info_df.iloc[index,4].replace("[","").replace("'","").replace("]","")
    if score == "unknow": 
        search = Anime(uid)
        score = search.score
        synopsis = search.synopsis.replace("[Written by MAL Rewrite]","")
        aired = search.aired
        genre = search.genres
        return synopsis,score,genre,aired

    else:
        return synopsis,score,genre,aired

@app.route("/Recommend",methods =["POST"])
def recommend():
    anime = request.form["anime"]
    if anime == "":
        return render_template("entererror.html")
    else:
        if df[df['title'] == anime].empty:
            search = AnimeSearch(anime)
            anime = search.results[0].title
            uid = search._results[0].mal_id
            suggestions = get_suggestions()
            if df[df['title'] == anime].empty:
                new_main_all = only_anime(anime)
                mal_id = new_main_all[2]
                all_names = rec_name(mal_id)[0:10]
                all_posters = all_names.apply(fetch_poster)
                all_comments = fetch_comment(mal_id)
                return render_template("index.html",main_name = new_main_all[0],main_poster = new_main_all[1],suggestions =  suggestions,
                score = new_main_all[4],genre = new_main_all[3],synopsis = new_main_all[5],aired = new_main_all[6],
                anime_name1 = all_names[0],poster_url1 = all_posters[0],
                anime_name2 = all_names[1],poster_url2 = all_posters[1],
                anime_name3 = all_names[2],poster_url3 = all_posters[2],
                anime_name4 = all_names[3],poster_url4 = all_posters[3],
                anime_name5 = all_names[4],poster_url5 = all_posters[4],
                anime_name6 = all_names[5],poster_url6 = all_posters[5],
                anime_name7 = all_names[6],poster_url7 = all_posters[6],
                anime_name8 = all_names[7],poster_url8 = all_posters[7],
                anime_name9 = all_names[8],poster_url9 = all_posters[8],
                anime_name10 = all_names[9],poster_url10 = all_posters[9],
                comment1 = all_comments[0],comment2 = all_comments[1],comment3 = all_comments[2],uid = mal_id,link = all_comments[3])
            else:
                index = df[df['title'] == anime].index[0]
        else:
            index = df[df['title'] == anime].index[0]
        suggestions = get_suggestions()
        uid = info_df.iloc[index,1]
        all_comments = fetch_comment(uid)
        comment1 = all_comments[0]
        comment2 = all_comments[1]
        comment3 = all_comments[2]
        main_poster = fetch_poster(anime)
        score = main_info(anime)[1]
        genre = main_info(anime)[2]
        synopsis = main_info(anime)[0]
        aired = main_info(anime)[3]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
        recommended_anime_names = []
        recommended_anime_posters = []
        for i in distances[1:11]:
            recommended_anime_posters.append(fetch_poster(df.iloc[i[0]].title))
            recommended_anime_names.append(df.iloc[i[0]].title)
        return render_template("index.html",main_name = anime,main_poster = main_poster,suggestions =  suggestions,
        score = score,genre = genre,synopsis = synopsis,aired = aired,link = all_comments[3],
        anime_name1 = recommended_anime_names[0],poster_url1 = recommended_anime_posters[0],
        anime_name2 = recommended_anime_names[1],poster_url2 = recommended_anime_posters[1],
        anime_name3 = recommended_anime_names[2],poster_url3 = recommended_anime_posters[2],
        anime_name4 = recommended_anime_names[3],poster_url4 = recommended_anime_posters[3],
        anime_name5 = recommended_anime_names[4],poster_url5 = recommended_anime_posters[4],
        anime_name6 = recommended_anime_names[5],poster_url6 = recommended_anime_posters[5],
        anime_name7 = recommended_anime_names[6],poster_url7 = recommended_anime_posters[6],
        anime_name8 = recommended_anime_names[7],poster_url8 = recommended_anime_posters[7],
        anime_name9 = recommended_anime_names[8],poster_url9 = recommended_anime_posters[8],
        anime_name10 = recommended_anime_names[9],poster_url10 = recommended_anime_posters[9],
        comment1 = comment1,comment2 = comment2,comment3 = comment3,uid = uid)


if __name__ == "__main__":
    app.run(debug=True)
