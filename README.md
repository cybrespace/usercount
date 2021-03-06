Mastodon User Count Bot
=======================

A bot which counts users from all instances listed at [https://instances.mastodon.xyz]
then posts statistics to [Mastodon](https://github.com/tootsuite/mastodon).

My copy is currently running at https://social.lou.lt/@mastodonusercount

This is a variation of the bot by @josefkenny: https://github.com/josefkenny/usercount

### Dependencies

-   **Python 2**
-   [gnuplot](http://www.gnuplot.info/) version 5 or greater
-   [Mastodon.py](https://github.com/halcy/Mastodon.py): `pip install Mastodon.py`
-   Everything else at the top of `usercount.py`!

### Usage:

1. Edit `config.txt` to specify the hostname of the Mastodon instance you would like to get data from.
2. Create a file called `secrets.txt` in the folder `secrets/`, as follows:

```
uc_client_id: <your client ID>
uc_client_secret: <your client secret>
uc_access_token: <your access token>
```

To get these values, create an account for your bot, then run this script:

```python
from mastodon import Mastodon

# change this to the apprpriate instance, login and username
instance_url = "https://mastodon.social"
user_name = "youremail@example.com"
user_password = "123456"

Mastodon.create_app("My User Count", scopes=["read","write"],
   to_file="clientcred.txt", api_base_url=instance_url)

mastodon = Mastodon(client_id = "clientcred.txt", api_base_url = instance_url)
mastodon.log_in(
   user_name,
   user_password,
   scopes = ["read", "write"],
   to_file = "usercred.txt"
)
```

Your client id and secret are the two lines in `clientcred.txt`, your access
token is the line in `usercred.txt`. (Yeah, I know I should have automated this step --
but hey, the above script is better than having to figure it out by yourself! ;) )

3. Use your favourite scheduling method to set `./usercount.py` to run regularly.

Call the script with the `--no-upload` argument if you don't want to upload anything.

Note: The script will fail to output a graph until you've collected data points that are actually different!
