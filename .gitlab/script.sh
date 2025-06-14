#!/bin/bash
# exit when any command fails
set -e
# echo on
set -x
python cds_paper_bot.py -m 1 -e "${EXPERIMENT}" --arXiv
if [[ -n $(git status -s) ]]; then
    git checkout master
    git add ./*_FEED.txt
    git commit -m "update tweeted analyses"
    git remote set-url origin "${REMOTE_GIT_REPO}"
    git remote -v
    # Update before pushing to avoid conflicts with commits at the same time
    # The old 'git pull origin master' is replaced by the following logic:

    echo "Fetching from origin/master..."
    git fetch origin master
    if [ $? -ne 0 ]; then
        echo "Failed to fetch from origin/master. Exiting."
        exit 1
    fi

    echo "Attempting to rebase local changes onto origin/master..."
    # Temporarily disable exit on error for the rebase command itself,
    # as a non-zero exit code indicates conflicts to be resolved or other rebase issues.
    set +e
    git rebase origin/master
    REBASE_EXIT_CODE=$?
    set -e # Re-enable exit on error

    if [ ${REBASE_EXIT_CODE} -ne 0 ]; then
        echo "Initial git rebase command failed with exit code ${REBASE_EXIT_CODE}."
        echo "This often means there are conflicts to resolve. Attempting to auto-resolve for *_FEED.txt files."
        
        CONFLICTING_FILES=$(git diff --name-only --diff-filter=U)
        if [ -z "$CONFLICTING_FILES" ]; then
            echo "Rebase failed, but no conflicting files (status 'U') found. Current git status:"
            git status
            echo "Aborting rebase as the cause of failure is unclear."
            # Ensure we are in a rebase process before aborting
            if [ -d "$(git rev-parse --git-dir)/rebase-merge" ] || [ -d "$(git rev-parse --git-dir)/rebase-apply" ]; then
                git rebase --abort
            else
                echo "Not currently in a rebase process, despite rebase command failure. Exiting."
            fi
            exit 1
        fi

        echo "Conflicting files found: $CONFLICTING_FILES"
        ALL_USER_CONFLICTS_RESOLVED=true # Flag to track if all relevant conflicts are handled

        for FILE in $CONFLICTING_FILES; do
            if [[ "$FILE" == *"_FEED.txt" ]]; then
                echo "Resolving conflict in $FILE by taking the union of lines..."
                TEMP_MERGED_FILE=$(mktemp)
                # Attempt to get content from "our" commit (:2) and "their" commit (:3)
                # Redirect stderr to /dev/null for git show in case a stage doesn't exist (e.g. file add vs content)
                # The overall command's success is checked.
                if ! ( (git show :2:"$FILE" 2>/dev/null; git show :3:"$FILE" 2>/dev/null) | sort -u > "$TEMP_MERGED_FILE" ); then
                    echo "ERROR: Failed to create sorted union for $FILE. Temp file content might be incomplete or empty."
                    rm -f "$TEMP_MERGED_FILE" # Clean up temp file
                    ALL_USER_CONFLICTS_RESOLVED=false
                    break # Stop processing files
                fi
                
                # Overwrite the original file with the merged content
                if ! mv "$TEMP_MERGED_FILE" "$FILE"; then
                    echo "ERROR: Failed to move temporary merged file to $FILE."
                    rm -f "$TEMP_MERGED_FILE" # Ensure cleanup if mv fails
                    ALL_USER_CONFLICTS_RESOLVED=false
                    break # Stop processing files
                fi
                
                echo "Successfully created merged content for $FILE. Staging..."
                if ! git add "$FILE"; then
                    echo "ERROR: Failed to 'git add $FILE' after resolving conflict."
                    ALL_USER_CONFLICTS_RESOLVED=false 
                    break # Stop processing files
                fi
                echo "Conflict in $FILE resolved and staged."
            else
                echo "Conflict in file '$FILE' is not a *_FEED.txt file. Cannot automatically resolve."
                ALL_USER_CONFLICTS_RESOLVED=false
                break # Stop processing files, as manual intervention would be needed
            fi
        done

        if [ "$ALL_USER_CONFLICTS_RESOLVED" = true ]; then
            echo "All relevant conflicts processed for auto-resolution. Continuing rebase..."
            set +e
            git rebase --continue
            REBASE_CONTINUE_EXIT_CODE=$?
            set -e

            if [ ${REBASE_CONTINUE_EXIT_CODE} -ne 0 ]; then
                echo "git rebase --continue failed with exit code ${REBASE_CONTINUE_EXIT_CODE}."
                echo "This could be due to remaining conflicts not auto-resolved, empty commits, or other issues."
                echo "Aborting rebase."
                if [ -d "$(git rev-parse --git-dir)/rebase-merge" ] || [ -d "$(git rev-parse --git-dir)/rebase-apply" ]; then
                    git rebase --abort
                fi
                exit 1
            else
                echo "Rebase continued and completed successfully."
            fi
        else
            echo "Not all conflicts could be automatically resolved or an error occurred during resolution. Aborting rebase."
            if [ -d "$(git rev-parse --git-dir)/rebase-merge" ] || [ -d "$(git rev-parse --git-dir)/rebase-apply" ]; then
                git rebase --abort
            fi
            exit 1
        fi
    else
        echo "Rebase completed successfully without conflicts, or no local commits to rebase."
    fi
    
    # ssh -v git@gitlab.cern.ch -p 7999
    git push origin HEAD
else
    echo "No changes found."
fi
