if [ "$1" == "" ]; then
    echo "Updating database (not initializing) by default"
    python3 init_db.py
    echo "Finished Updating"
else
    if [ "$1" != "-init" ]; then
        echo "Couldn't recognize your command $1, please try again latter"
    else
        echo "Initializing the database...."
        sqlite3 auto_quiz.db < schema.sql
        echo "Finished initializing"
        python3 init_db.py
        echo "Finished loading content"
    fi
fi