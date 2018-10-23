# NOMIC_scripts

To rsync stuff from the NOMIC scripts directory, run
rsync -vr --include="*/" --include="*.pro" --exclude="*" observer@lbti-nomic:~/scripts_obs/* .
