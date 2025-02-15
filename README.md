# The Sandbox Accounts Checker

Hello!

In this repository, you will find code for convenient account checking in the game **The Sandbox**.
By running the script with proxy support, you can quickly extract the necessary account information.
In the current version (v1.0.0), you receive a private key checker that saves data in the following format:

```
privatekey | TSB_username | banned=? | items_amount=? | datetime
```

Thus, by running this script, after a while you will obtain a table with information about all your accounts.

## Quick Start Guide

1. **Install Python**  
   Download and install Python. This tool was developed and tested on **Python 3.12.7**.

2. **Initial Setup**  
   Run the `first_start.py` file from the console (run as Administrator if your operating system requires it).  
   This will create all the necessary files and install the required dependencies.

   ```bash
   python first_start.py
   ```

3. **Configure Proxies**  
   Insert proxies in the format `IP:PORT:USER:PASSWORD`, one per line, into the `proxies.txt` file.  
   For example:

   ```
   192.168.1.1:8080:myUserName:BestPassword!
   001.123.4.5:30303:user2:pass2
   ```

4. **Configure Private Keys**  
   Insert private keys, one per line, into the `privatekeys.txt` file (
Ignore the presence of the 0x prefix).

5. **Run the Main Script**  
   Run `main.py` and enjoy. (It is recommended to run it from the command line to see logs and errors.)

   ```bash
   python main.py
   ```

6. **Check the Results**  
   After the script completes, review the following files:
   - **results.txt** — contains all the collected data.
   - **unbanned.txt** — contains the same data filtered to show only accounts that are not banned.

---

Made with ❤️ by T1mQa
