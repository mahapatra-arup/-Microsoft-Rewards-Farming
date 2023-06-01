SET mypath=%~dp0
cd %mypath%
python -i ms_rewards_farmer.py --superfast --skip-unusual --session
::--edge --incognito