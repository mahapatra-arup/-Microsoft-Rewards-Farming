# -Microsoft-Rewards-Farming

<!DOCTYPE html>
<html>
	<head>
		<title>Microsoft-Rewards-Farming</title>
	</head>
	<body>
		<p>Installation 
Install requirements with the following command : 
pip install -r requirements.txt 
Make sure you have Chrome installed (unless your using --edge) 
Edit the accounts.json.sample with your accounts credentials and rename it by removing .sample at the end. 
If you want to add more than one account, the syntax is the following (mobile_user_agent, proxy and goal are optional). Remove mobile_user_agent, proxy or goal from your account if you don't know how to use them: 
[ 
    { 
        "username": "Your Email", 
        "password": "Your Password", 
        "totpSecret": "Your TOTP Secret (optional)", 
        "mobile_user_agent": "your preferred mobile user agent", 
        "proxy": "HTTP proxy (IP:PORT)", 
        "goal": "Amazon" 
    }, 
    { 
        "username": "Your Email 2", 
        "password": "Your Password 2", 
        "totpSecret": "Your TOTP Secret (optional)", 
        "mobile_user_agent": "your preferred mobile user agent", 
        "proxy": "HTTP proxy (IP:PORT)", 
        "goal": "Xbox Game Pass Ultimate" 
     } 
]    
Due to the limits of Ipapi, it may return an error and cause the bot to stop. You can define the default language and location to prevent it from crashing here.</p>
	</body>
</html>

