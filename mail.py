import discord
import imaplib
import email
import config
import re

mail = imaplib.IMAP4_SSL(config.server)
mail.login(config.username, config.password)
mail.list()

def get(toCheck = 3):
    # Out: list of "folders" aka labels in gmail.
    mail.select("inbox") # connect to inbox.
    output = []

    result, data = mail.search(None, "ALL")

    ids = data[0] # data is a list.
    id_list = ids.split() # ids is a space separated string

    for i in range(toCheck):

        selector = -i - 1
        try:
            latest_email_id = id_list[selector] # get the latest


            result, data = mail.fetch(latest_email_id, "(RFC822)") # fetch the email body (RFC822) for the given ID


            raw_email = data[0][1].decode('utf-8') # here's the body, which is raw text of the whole email
            # including headers and alternate payloads

            msg = email.message_from_string(raw_email)

            regexphrase = "[A-Za-z0-9.-]*@[A-Za-z0-9.-]*." + config.universityDomain # I should maube add more than this, but I haven't seen any AAU emails with other characters than that \shrug
            msgFromAdress = msg['From'].split()[-1][1:-1]

            if re.match(regexphrase, msgFromAdress) is not None:
                for part in msg.walk():
                    # each part is a either non-multipart, or another multipart message
                    # that contains further parts... Message is organized like a tree
                    if part.get_content_type() == 'text/plain':
                        output.append({
                            "passphrase": part.get_payload().split()[0],
                            "email": msgFromAdress
                        }) # prints the raw text

        except IndexError as e:
            pass

        return output

def check(database, discordClient, toCheck = 3):
    data = get(toCheck)
    for entry in data:
        if not database.emailUsed(entry["email"]):
            pphrase = re.sub('[^0-9a-zA-Z]+', '', entry['passphrase'])
            if database.passphraseExists(pphrase):

                username = database.getPassphrase(pphrase)["username"]
                userId = database.getPassphrase(pphrase)["id"]
                emailAddress = entry["email"]

                database.verify(userId, emailAddress)

                server = discordClient.get_server(config.discordServer)
                user = server.get_member(userId)

                print("Verified user '%s' with email address '%s'" % (username, emailAddress))

                return user

    return False
