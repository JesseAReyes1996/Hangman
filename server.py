#Written using Python 3.6.1
import errno
import os
import random
import socket
import sys
from time import sleep
from _thread import *

WORDS = ["rain","apple","soft","gypsy","beyond","escape","eclipse","opossum","gryffindor","trailer"]

CLIENTS = {} #conn.fileno():conn
USERNAMES = [] #List of usernames
CONNECTEDUSERS = {} #conn:username
USERCONN = {} #username:conn
SCORE = {} #username:score
PASSWORDS = {} #username:password
GAMESLIST = {} #Host name:list of conns in game
GUESSDICT = {} #Host name:list of guesses from users in game

HOST = ''   # Symbolic name meaning all available interfaces
PORT = 8238 # Arbitrary non-privileged port

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#bind the socket to the port given, ensure that all incoming data which is
#directed towards this port number is received by this application
try:
    s.bind((HOST, PORT))

except socket.error as msg:
    print("Bind failed. Error Code : " + str(msg[0]) + " Message " + msg[1])
    sys.exit()

s.listen(10)

#Clear the screen
def clear(*args):
    #Clear server-side terminal
    if(len(args) == 0):
        os.system("clear")
    #Clear client side terminal
    elif(len(args) == 1):
        #ANSI sequence to clear screen
        args[0].sendall("\033[2J".encode("utf-8"))
        #ANSI sequence to move cursor back to home
        args[0].sendall("\033[H".encode("utf-8"))

#For receiving data from client when in-game
def nonblockRecv(conn):
    try:
        data = conn.recv(1024)
    except socket.error as e:
        err = e.args[0]
        if(err == errno.EAGAIN or err == errno.EWOULDBLOCK):
            sleep(0.01)
            #Guess is set to 'Ø' because it is a special character not found on
            #most keyboards
            guess = 'Ø'
        else:
            print(e)
            sys.exit()
    else:
        guess = str(data[:-2], "utf-8").lower()
    return guess

#Receive a reply from client when in menus
def clientRecv(conn):
    data = conn.recv(1024)
    reply = str(data[:-2], "utf-8")

    if not(data):
        print("ERROR: CLIENT RECEIVE")
    return reply

#Send a message to the client
def clientSend(msg, conn):
    conn.sendall(msg.encode("utf-8"))

def formatLayout(guesses, incorrectGuesses, users, turn):
    layout = ""
    #Format correct guesses
    for i in guesses:
        layout += i + " "
    layout += "\n\n"
    #Format incorrect guesses
    for i in incorrectGuesses:
        layout += i + " "
    layout += "\n\n"
    #Print players who are playing and also whose turn it is
    for idxI, i in enumerate(users):
        if(idxI == turn):
            layout += CONNECTEDUSERS[i].capitalize() + ' ' + str(SCORE[CONNECTEDUSERS[i]]) + ' *' + '\n'
        else:
            layout += CONNECTEDUSERS[i].capitalize() + ' ' + str(SCORE[CONNECTEDUSERS[i]]) + '\n'
    #In the event that all users lost, don't send extra newline
    if(users):
        layout += "\n"
    return layout

#For a user to join a running game
def joinGame(conn, host):
    #Give the newGame thread time to initialize the inGame list
    if(CONNECTEDUSERS[conn] == host):
        sleep(0.1)
    #Insert user into game of their choice
    GAMESLIST[host].append(conn)
    #Give the connecting user a score of 0
    SCORE[CONNECTEDUSERS[conn]] = 0
    #Make the connection non-blocking
    conn.setblocking(False)
    clientSend("Waiting to join...", conn)
    #Allow them to play until they're removed from the game
    while(conn in GAMESLIST[host]):
        guess = nonblockRecv(conn)
        #When they enter a guess send it to the game
        if(guess != 'Ø'):
            #Append the username of guesser
            guess += '|' + CONNECTEDUSERS[conn]
            GUESSDICT[host].append(guess)
    sleep(3)
    conn.setblocking(True)

def newGame(difficulty, conn):
    #word = random.choice(WORDS)TODO
    word = "trailer"
    if(difficulty == "1"):
        guessesAllowed = len(word) * 3
    elif(difficulty == "2"):
        guessesAllowed = len(word) * 2
    elif(difficulty == "3"):
        guessesAllowed = len(word) * 1

    #Assign the user who started the new game to be the host
    host = CONNECTEDUSERS[conn]
    inGame = []
    GAMESLIST[host] = inGame
    turn = 0
    #List to hold user's guesses
    GUESSDICT[host] = []

    #Fill array with n underscores, where n is the length of the word
    guesses = ["_"] * len(word)
    guessCnt = 0
    incorrectGuesses = []

    #While no one has entered the game yet
    while not GAMESLIST[host]:
        continue

    #Send the default layout of the game
    for i in GAMESLIST[host]:
        clear(i)
    layout = formatLayout(guesses, incorrectGuesses, GAMESLIST[host], turn)
    for i in GAMESLIST[host]:
        clientSend(layout, i)

    win = False
    #While the users haven't used all of their allotted guesses
    while guessCnt < guessesAllowed:
        guess = 'Ø'
        #If any user guessed, retrieve it from GUESSDICT
        if(host in GUESSDICT):
            #Get most recently sent guess
            for i in GUESSDICT[host]:
                #The variable "guess" has the user's guess in it, as well as the username of
                #who made the guess
                guess = i

        #When screen is cleared, user input is not cleared TODO

        #BUG TODO
        #starter a l
        #joiner guesses full word

        #No guesses have been made
        if(guess == 'Ø'):
            continue

        #If user sends nothing don't count as a guess
        if(guess[0] == '|'):
            layout = formatLayout(guesses, incorrectGuesses, GAMESLIST[host], turn)
            clear(USERCONN[guess[1:]])
            clientSend(layout, USERCONN[guess[1:]])
            GUESSDICT[host].pop()
            continue

        #Give each player a turn to guess
        #print(turn)#TODO
        playerTurn = CONNECTEDUSERS[GAMESLIST[host][turn]]
        #Increment only if the player whose turn it is guessed
        if((playerTurn == guess.split('|')[1])):
            turn += 1

        #Check if user is trying to guess the word
        if(guess[1] != '|'):
            user = guess.split('|')[1]
            guess = guess.split('|')[0]
            GUESSDICT[host].pop()
        #If the player whose turn it is guessed, check if their guess was
        #correct
        elif(playerTurn == guess.split('|')[1]):
            user = guess.split('|')[1]
            guess = guess.split('|')[0]
            GUESSDICT[host].pop()
        #If it is not the user's turn, ignore input
        else:
            clear(USERCONN[guess.split('|')[1]])
            layout = formatLayout(guesses, incorrectGuesses, GAMESLIST[host], turn)
            clientSend(layout, USERCONN[guess.split('|')[1]])
            GUESSDICT[host].pop()
            continue

        #If user sends a non-alpha don't count as a guess
        if not(guess.isalpha()):
            #Check if the host is inputting a character which would otherwise
            #mess up the turn variable by causing it to become negative TODO
            if not(turn == 0):
                turn -= 1
            layout = formatLayout(guesses, incorrectGuesses, GAMESLIST[host], turn)
            for i in GAMESLIST[host]:
                clear(i)
                clientSend(layout, i)
            continue

        #Bool to check whether the guess was correct or not
        inWord = False
        #Check to see if user entered only one letter
        if(len(guess) == 1):
            position = 0
            #Check if guessed letter is in word
            for letter in word:
                if(guess == letter):
                    #Mark that their guess is in the word
                    inWord = True
                    #Replace underscore with correct letter
                    guesses[position] = guess
                position += 1
            #User gets to guess again and score is increased by one
            if(inWord):
                turn -= 1
                SCORE[user] += 1
            #Check to see if user has correctly guessed the word
            check = ""
            for i in guesses:
                check += i
            if(check == word):
                win = True
                winner = user
                break

            #If the guess was incorrect, increment user's guess count
            if not(inWord):
                #If user guesses a letter that is already incorrect don't
                #increment guess count
                if guess not in incorrectGuesses:
                    guessCnt += 1
                    incorrectGuesses.append(guess)
        #User entered a word
        else:
            if(guess == word):
                win = True
                winner = user
                #Format so that a win by whole word is reflected by the layout
                for i in word:
                    position = 0
                    for j in word:
                        if(i == j):
                            guesses[position] = i
                        position += 1
                break
            else:
                #Send message to user telling them that they lost
                #Send final state of the game before they lost
                layout = formatLayout(guesses, incorrectGuesses, GAMESLIST[host], turn)
                layout += "Game Over\n"
                clear(USERCONN[user])
                clientSend(layout, USERCONN[user])
                GAMESLIST[host].remove(USERCONN[user])

                #In the event no users are left in the game
                if not(GAMESLIST[host]):
                    break

        #Reset turn to first player when all other players have guessed
        if(len(GAMESLIST[host]) <= turn):
            turn = 0

        #Send game layout to all users in game
        layout = formatLayout(guesses, incorrectGuesses, GAMESLIST[host], turn)
        for i in GAMESLIST[host]:
            clear(i)
            clientSend(layout, i)

    if(win):
        #Send message to users telling them who won
        #Send final state of the game before user won
        SCORE[winner] += len(word)
        layout = formatLayout(guesses, incorrectGuesses, GAMESLIST[host], turn)
        layout += winner.capitalize() + " Won"
        print(GAMESLIST[host]) #TODO
        for i in GAMESLIST[host]:
            clear(i)
            clientSend(layout, i)
            GAMESLIST[host].remove(i)#MAYBE HERE? TODO

    #Users ran out of guesses
    else:
        #Send message to users telling them that they lost
        #Send final state of the game before they lost
        layout = formatLayout(guesses, incorrectGuesses, GAMESLIST[host], turn)
        layout += "Game Over\n"
        for i in GAMESLIST[host]:
            clear(i)
            clientSend(layout, i)
            GAMESLIST[host].remove(i)

    sleep(3)

    if(len(GAMESLIST[host]) == 0):
        GAMESLIST.pop(host)
    #sleep(3)

def gameMenu(conn):
    while True:
        clear(conn)
        #Send game menu to the connected client
        clientSend("1. Start New Game\n2. Join existing game\n3. Hall of Fame\n4. Log Out\n", conn)
        #Receive reply from client
        reply = clientRecv(conn)

        #User starts new game
        if(reply == "1"):
            #Only allow user to enter 1, 2, or 3 to choose their difficulty
            diffChosen = False
            while not diffChosen:
                clear(conn)
                #Ask user to choose their difficulty for the game
                clientSend("Choose difficulty:\n1. Easy\n2. Medium\n3. Hard\n", conn)
                difficulty = clientRecv(conn)

                if(difficulty == "1" or difficulty == "2" or difficulty == "3"):
                    diffChosen = True
            start_new_thread(newGame, (difficulty, conn, ))
            joinGame(conn, CONNECTEDUSERS[conn])

        #User joins a currently running game
        elif(reply == "2"):
            clear(conn)
            #Print list of hosts to join
            for idxI, i in enumerate(GAMESLIST.keys()):
                clientSend(str(idxI + 1) + ". " + i + "'s game\n", conn)
            clientSend("\nEnter the name of the host of the game you wish to join\n", conn)
            host = clientRecv(conn)
            host = host.lower()
            #Check that host entered is valid
            for i in GAMESLIST.keys():
                if(i == host):
                    joinGame(conn, host)
                    break

        #User logs out
        elif(reply == "4"):
            clear(conn)
            user = CONNECTEDUSERS[conn]
            del CONNECTEDUSERS[conn]
            del USERCONN[user]
            break

def mainMenuThread(conn):

    while True:
        clear(conn)
        #Send main menu to the connected client
        clientSend("Main Menu\n\n1. Login\n2. Register\n3. Hall of Fame\n4. Exit\n", conn)
        #Receive reply from client
        reply = clientRecv(conn)

        #User login
        if(reply == "1"):
            clear(conn)
            clientSend("Username: ", conn)
            user = clientRecv(conn)
            user = user.lower()
            clientSend("Password: ", conn)
            password = clientRecv(conn)
            #If the username entered is registered
            if(user in USERNAMES):
                #If the user is not already logged in
                if(user not in CONNECTEDUSERS.values()):
                    #If the password is correct
                    if(PASSWORDS[user] == password):
                        #Add to dictionary of currently logged in users
                        CONNECTEDUSERS[conn] = user
                        #Dictionary to lookup conn by username
                        USERCONN[user] = conn
                        #Transition to game menu once logged in
                        gameMenu(conn)
                        pass
                    #The password entered was incorrect
                    else:
                        clientSend("The password you've entered is incorrect", conn)
                        sleep(1)
                #The user is already logged in
                else:
                    clientSend("User is already logged in", conn)
                    sleep(1)
            #The username entered is not registered
            else:
                clientSend("Sorry, we did not find an account with that username", conn)
                sleep(1)

        #Register a new user
        elif(reply == "2"):
            clear(conn)
            clientSend("Username: ", conn)
            newUser = clientRecv(conn)
            newUser = newUser.lower()
            clientSend("Password: ", conn)
            newPass = clientRecv(conn)
            #Username is already taken
            if(newUser in USERNAMES):
                clientSend("Username is already taken", conn)
                sleep(1)
            #Register user if user not already taken
            else:
                USERNAMES.append(newUser)
                PASSWORDS[newUser] = newPass

        #Display the top 10 scores of all time
        elif(reply == "3"):
            print("Hall of Fame")

        #User exits the connection
        elif(reply == "4"):
            clear(conn)
            del CLIENTS[conn.fileno()]
            conn.close()
            break

    conn.close()

#Server-side admin menu
def serverThread():

    while True:
        clear()
        print("Server Admin Menu")
        print("1. Current list of connected users")
        print("2. Current list of registered users")
        print("3. Current list of words")
        print("4. Add new word")
        action = input()

        #Print list of currently logged in users
        if(action == "1"):
            clear()
            for i in CONNECTEDUSERS.values():
                print(i)
            input("Press Enter to continue...")
        #Print list of registered users
        elif(action == "2"):
            clear()
            for i in USERNAMES:
                print(i)
            input("Press Enter to continue...")
        #Print list of current words available for play
        elif(action == "3"):
            clear()
            for i in WORDS:
                print(i)
            input("Press Enter to continue...")
        elif(action == "4"):
            clear()
            word = input("Enter a new word: ")
            #If the word is not already in the list and the word only contains
            #letters then add it to the list of words
            if(word.lower() not in WORDS and word.isalpha()):
                WORDS.append(word.lower())


#Start server-side thread
start_new_thread(serverThread, ())

while 1:

    #Wait to accept a connection - blocking call
    conn, addr = s.accept()

    #Add client to dictionary
    CLIENTS[conn.fileno()] = conn

    #Start new thread for every client that connects
    start_new_thread(mainMenuThread, (conn, ))

s.close()
