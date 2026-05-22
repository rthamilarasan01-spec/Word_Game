from flask import Flask,request,redirect,render_template,jsonify
from flask_sqlalchemy import SQLAlchemy
import random
import json

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/word_game'

db =SQLAlchemy(app)

class Players(db.Model):
    player_id = db.Column(db.String(50), primary_key=True)
    score = db.Column(db.Integer)
    average = db.Column(db.String(20))
    rank = db.Column(db.Integer)
    time = db.Column(db.String(50))

with app.app_context():
    db.create_all()

player_data = ''

with open('word_json.json', 'r') as f:
    dictionary = json.load(f)

levels = []

for value in dictionary.values():
    levels.append(tuple(value))

level1 = levels[0]
level2 = levels[1]
level3 = levels[2]

temp=set()
def play_game(level):
    global temp
    word=''
    temp_dict={}
    while True:
        if level==1:
            word=random.choice(level1)
            if len(temp)==len(level1):
                temp.clear()
        elif level==2:
            word=random.choice(level2)
            if len(temp)==len(level2):
                temp.clear()
        elif level==3:
            word=random.choice(level3)
            if len(temp)==len(level3):
                temp.clear()
        if word not in temp:
            temp.add(word)
            break
        else:
            continue
    dummy_word=['_' for _ in range(len(word))]
    if len(word)%2==0:
        no=int(len(word)/2)
    else:
        no=round(len(word)/2)+1
    for i in range(no):
        while True:
            ind = random.randint(0,len(word) - 1)
            if str(ind) not in temp_dict:
                temp_dict.update({str(ind):word[ind]})
                break
            else:
                 continue
    for k,v in temp_dict.items():
        dummy_word[int(k)]=v
    display_word=''
    for i in dummy_word:
        display_word+=i+' '
    return word,display_word

@app.route('/')
def home():
    return render_template('login.html')


@app.route('/login/<player>')
def login(player):
    check_player = db.session.query(Players.player_id).all()
    player_list = [i[0] for i in check_player]
    if player in player_list:
        return render_template('main.html', player=player)
    else:
        player = 'Player id does not exists'
        return render_template('login.html', player=player)
    
@app.route('/new_login/<player>')
def new_login(player):
    check_player = db.session.query(Players.player_id).all()
    player_list = [i[0] for i in check_player]
    if player in player_list:
        player = 'Player id already exists try another'
        return render_template('login.html', new_player=player)
    else:
        player_data = Players(
            player_id = player
        )
        db.session.add(player_data)
        db.session.commit()
    return render_template('main.html', player=player)

@app.route('/level/<player>')
def level(player):
    return render_template('choose_level.html', player=player)

@app.route('/game/<level>/<player>')
def start_game(level,player):
    exp = ""
    if level == 'Easy':
        word,exp = play_game(1)
        exp = exp.upper()
        exp = '( ' +exp+ ' )'
    elif level == 'Medium':
        word,exp = play_game(2)
        exp = exp.upper()
        exp = '( ' +exp+ ' )'
    else:
        word,exp = play_game(3)
        exp = exp.upper()
        exp = '( ' +exp+ ' )'
    return render_template('game.html', 
                           level=level,
                           exp=exp,
                           player=player,
                           word=word
                           )

@app.route('/update', methods=['GET','POST'])
def update():
    game_data = request.get_json()
    count = int(game_data['count'])
    score = int(game_data['score'])
    answer = game_data['answer'].strip()
    level = game_data['level']
    exp = game_data['exp']
    new_exp = ""
    status = ''
    if level == 'Easy':
        word,old_exp = play_game(1)
        old_exp = old_exp.upper()
        new_exp = '( ' +old_exp+ ' )'
    elif level == 'Medium':
        word,old_exp = play_game(2)
        old_exp = old_exp.upper()
        new_exp = '( ' +old_exp+ ' )'
    else:
        word,old_exp = play_game(3)
        old_exp = old_exp.upper()
        new_exp = '( ' +old_exp+ ' )'

    if answer.lower() == exp:
        status = 'Correct'
        new_count = count+1
        new_score = score+5
    else:
        status = str(f'Incorrect. The Right Word is: {exp.upper()}')
        new_count = count+1
        new_score = score
    return jsonify({
        'new_count':new_count,
        'new_score':new_score,
        'new_exp':new_exp,
        'status':status,
        'word':word
    })

@app.route('/back/<player>')
def go_back(player):
    return render_template('main.html', player=player)

@app.route('/score_card', methods=['GET','POST'])
def score_card():
    score_card = request.get_json()
    score = int(score_card['score'])
    count = int(score_card['count'])
    level = score_card['level']
    time = score_card['time']
    player = score_card['player']
    average =''

    if score ==0:
        average = '0%'
    else:
        average = str(round(score/count*20,2))+'%'
    values = Players.query.get(player)
    if values.score:
        if score >= values.score:
            values.score = score
            values.average = average
            values.time = time
            db.session.commit()
    else:
        values.score = score
        values.average = average
        values.time = time
        db.session.commit()
    return render_template('score_card.html', 
                           final_score=score,
                           final_count=count,
                           final_level=level,
                           final_time=time,
                           final_average=average,
                           player=player
                           )

@app.route('/leaderboard')
def leader_board():
    players = Players.query.order_by(Players.score.desc()).all()

    rank = 1

    for player in players:
        player.rank = rank
        rank += 1

    db.session.commit()
    return render_template('leader_board.html', leader_board=players)

@app.route('/back_to_scorecard')
def back_to_scorecard():
    return redirect('/score_card')

if __name__ == '__main__':
    app.run(debug=True)