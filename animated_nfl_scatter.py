#!/usr/bin/env python
# coding: utf-8
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.animation as animation
import numpy as np
from PIL import Image
from os import listdir
import os
from IPython.display import HTML

def load_data():
    '''STEAL THE DATA FROM RON YURKOs GITHUB, thanks Ron, Maksim, and Sam!'''
    df = pd.DataFrame()

    for y in range(2009,2019):
        x = pd.read_csv("https://raw.githubusercontent.com/ryurko/nflscrapR-data/master/play_by_play_data/regular_season/reg_pbp_{}.csv".format(y), low_memory=False)
        #ADDS A SEASON COLUMN FOR LATER USE
        x['season'] = y
        df = df.append(x)
        
    return df

def cleanup_all_the_datas(df):
    df=df.copy(deep=True)
    
    #remove quarters ending, kickoffs, etc. 
    df = df.loc[
                    (df['epa'].notnull()) &
                    ((df['play_type'] == 'no_play') |
                    (df['play_type'] == 'pass') |
                    (df['play_type'] == 'run'))
                ]
    df.drop(df[(df['replay_or_challenge'] == 0) & (df['desc'].str.contains('Timeout'))].index, inplace=True)
    
    df = df.loc[df.desc.str.contains('kneels|spiked') == False]
    
    #RECLASSIFYING PENALTIES
    df['desc'].loc[df['play_type'] == 'no_play']
    
    df.loc[df.desc.str.contains('left end|left tackle|left guard|up the middle|right guard|right tackle|right end|rushes'),
    'play_type'] = 'run'

    df.loc[df.desc.str.contains('scrambles|sacked|pass'), 'play_type'] = 'pass'
    
    #RESET THE INDEX
    df.reset_index(drop=True, inplace=True)
    
    return df

def fix_rushers(df):
    df=df.copy(deep=True)
    
    rusher_nan = df.loc[(df['play_type'] == 'run') &
         (df['rusher_player_name'].isnull())]
         
    #Create a list of the indexes/indices for the plays where rusher_player_name is null
    rusher_nan_indices = list(rusher_nan.index)

    for i in rusher_nan_indices:
        #Split the description on the blank spaces, isolating each word
        desc = df['desc'].iloc[i].split()
        #For each word in the play description
        for j in range(0,len(desc)):
            #If a word is right, up, or left
            if desc[j] == 'right' or desc[j] == 'up' or desc[j] == 'left':
                #Set rusher_player_name for that play to the word just before the direction
                df['rusher_player_name'].iloc[i] = desc[j-1]     
            else:
                pass
            
    return df

def fix_passers(df):
        #Create a smaller dataframe with plays where passer_player_name is null
    passer_nan = df.loc[(df['play_type'] == 'pass') &
             (df['passer_player_name'].isnull())]
    #Create a list of the indexes/indices for the plays where passer_player_name is null
    passer_nan_indices = list(passer_nan.index)

    for i in passer_nan_indices:
        #Split the description on the blank spaces, isolating each word
        desc = df['desc'].iloc[i].split()
        #For each word in the play description
        for j in range(0,len(desc)):
            #If a word is pass
            if desc[j] == 'pass':
                df['passer_player_name'].iloc[i] = desc[j-1]            
            else:
                pass
    #Change any backwards passes that incorrectly labeled passer_player_name as Backward
    df.loc[df['passer_player_name'] == 'Backward', 'passer_player_name'] == float('NaN')
    
    return df

def load_and_clean_data():
    try:
        df = load_data()
    except:
        raise Exception('loading failed!')
    else:
        try:
            df = cleanup_all_the_datas(df)
        except:
            raise Exception('cleanup failed!')
        else:
            try:
                df = fix_rushers(df)
            except:
                raise Exception('fix rushers failed!')
            else:
                try: 
                    df = fix_passers(df)
                except:
                    raise Exception('fix passers failed!')
                else:
                    print("Ding! Datas done!")
                    return df

#######
### GETTING THE LOGOS TO WORK CORRECTLY
### Go here: https://github.com/jezlax/sports_analytics/tree/master/logos 
### Download those logos and put them in a directory called 'logos' and place that in your CWD
### the below code will call from that directory and loop over them for the scatterplots
### the logos from @statsbyLopez repo are too big for this scatter, and we can't scale them down since we're using 
### offsetbox to plot them at least AFAIK, if you have a better way to do it, get at me.
#######

def build_first_plot(df):
    def getImage(path): 
        return OffsetImage(plt.imread(path))

    logos = os.listdir(os.getcwd()+'\\logos')
    logolist = []
    for l in logos:
        logolist.append(os.getcwd()+'\\logos\\'+l)

    x = df['success']
    y = df['epa']

    fig, ax = plt.subplots(figsize=(10,10))
    ax.scatter(x, y, s=0.1)
    ax.set_title('Success Rate vs. EPA/Play',{"fontsize":24})
    ax.set_xlabel('Success Rate',{"fontsize":18})
    ax.set_ylabel('EPA/Play',{"fontsize":18})

    for x0, y0, path in zip(x, y, logolist):
        ab = AnnotationBbox(getImage(path), (x0, y0), frameon=False, fontsize=4)
        ax.add_artist(ab)


#BUILD THE ANIMATION, THIS WILL SAVE IT TO A MP4 FILE IN YOUR CURRENT DIRECTORY
def build_animation(df):
    x = [[] for i in range(10)]
    for i,j in zip(range(10), range(2009,2019)):
        x[i].append(df[df['season']==j]['epa'].values.tolist())
        
    y = [[] for i in range(10)]
    for i,j in zip(range(10), range(2009,2019)):
        y[i].append(df[df['season']==j]['success'].values.tolist())

    seasons = list(range(2009,2019))

    #DRAW THE FIGURE FIRST
    fig, ax = plt.subplots(figsize=(10,10))
    #ax.set_title('Success Rate vs. EPA/Play',{"fontsize":24})
    plt.title('data from nflscrapR',fontsize=16)
    plt.suptitle('Success Rate vs. EPA/Play',fontsize=24, y=0.945)
    ax.set_xlabel('Success Rate',{"fontsize":18})
    ax.set_ylabel('EPA/Play',{"fontsize":18})

    #ANIMATE OVER THE YEARS
    def animate(i):
        ax.clear()
        plt.xlim(-0.3,0.3)
        plt.ylim(0.3,0.6)
        def getImage(path): 
            return OffsetImage(plt.imread(path))

        logos = os.listdir(os.getcwd()+'\\logos')
        logolist = []
        for l in logos:
            logolist.append(os.getcwd()+'\\logos\\'+l)

        x_scatter = x[i][0]
        y_scatter = y[i][0]

        #fig, ax = plt.subplots(figsize=(10,10))
        ax.scatter(x_scatter, y_scatter, s=0.1)
        #ax.set_title('Success Rate vs. EPA/Play',{"fontsize":24})
        plt.title('data from nflscrapR',fontsize=16)
        ax.set_xlabel('Success Rate',{"fontsize":18})
        ax.set_ylabel('EPA/Play',{"fontsize":18})
        ax.text(-0.29,0.59, str(seasons[i]) + '-' + str(seasons[i]+1) + ' Season', fontsize=14)

        for x0, y0, path in zip(x_scatter, y_scatter, logolist):
            ab = AnnotationBbox(getImage(path), (x0, y0), frameon=False, fontsize=4)
            ax.add_artist(ab)
            
    ani = animation.FuncAnimation(fig, animate, frames=10, interval=2500)
    #plt.show()

    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=1, metadata=dict(artist='Me'), bitrate=1800)
    ani.save('animated_scatter.mp4', writer=writer)

    

df = load_and_clean_data()

#Get the dataset we need, specifically, EPA and Dropback success by team
## add success column
df['success'] = np.where(df['epa']>0,1,0)
 
# ## limit to pass plays
df[df['play_type'] == 'pass']

# ## group by team and season, avg epa and success rate
agg = df.groupby(['posteam','season'])[['epa','success']].mean().reset_index()

# #FIRST LETS MAKE IT JUST FOR 2018
agg18 = agg[agg['season']==2018]

#builds the standalone 2018 plot
build_first_plot(agg18)

#builds the animation
build_animation(agg)