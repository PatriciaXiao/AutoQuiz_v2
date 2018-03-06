if [ "$1" == "" ]; then
    echo "Updating database (not initializing) by default"
else
    if [ "$1" != "-init" ]; then
        echo "Couldn't recognize your command $1, please try again latter"
    else
        echo "Initializing the database...."
        sqlite3 auto_quiz.db < schema.sql
        echo "Finished initializing"
fi
    sqlite3 auto_quiz.db < schema.sql
fi

python init_db.py