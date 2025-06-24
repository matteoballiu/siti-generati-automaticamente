import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv

load_dotenv()

# Configura con la tua mail e app password dalle variabili d'ambiente
IMAP_SERVER = os.getenv("IMAP_HOST", "imap.gmail.com")  # Default a gmail se non specificato
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASSWORD")

if not IMAP_USER or not IMAP_PASS:
    print("Attenzione: IMAP_USER o IMAP_PASSWORD non sono impostate nelle variabili d'ambiente. La lettura email potrebbe fallire.")
    # Potresti voler lanciare un errore qui se la lettura email è critica:
    # raise ValueError("IMAP_USER e IMAP_PASSWORD devono essere impostate nelle variabili d'ambiente.")


def fetch_unread_emails():
    if not IMAP_USER or not IMAP_PASS:
        print("Credenziali IMAP non configurate. Impossibile leggere le email.")
        return []
        
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(IMAP_USER, IMAP_PASS)
        mail.select("inbox")
        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK':
            print(f"Errore nella ricerca email: {status}")
            mail.logout()
            return []

        email_ids = messages[0].split()
        emails = []
        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            if status != 'OK':
                print(f"Errore nel fetch dell'email ID {e_id}: {status}")
                continue
            
            msg = email.message_from_bytes(msg_data[0][1])
            subject_header = decode_header(msg["Subject"])
            subject = ""
            for s, encoding in subject_header:
                if isinstance(s, bytes):
                    subject += s.decode(encoding if encoding else "utf-8", errors="replace")
                else:
                    subject += s

            from_ = msg.get("From")
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if "attachment" not in content_disposition and content_type == "text/plain":
                        try:
                            charset = part.get_content_charset() or 'utf-8'
                            body = part.get_payload(decode=True).decode(charset, errors="replace")
                            break 
                        except Exception as e:
                            print(f"Errore nel decodificare una parte multipart: {e}")
                            # Prova a decodificare con un charset di fallback o ignora
                            try:
                                body = part.get_payload(decode=True).decode('latin-1', errors="replace")
                                break
                            except:
                                pass # Ignora se anche il fallback fallisce
            else: # Non multipart
                try:
                    charset = msg.get_content_charset() or 'utf-8'
                    body = msg.get_payload(decode=True).decode(charset, errors="replace")
                except Exception as e:
                    print(f"Errore nel decodificare il payload principale: {e}")
                    try:
                        body = msg.get_payload(decode=True).decode('latin-1', errors="replace")
                    except:
                        body = "Impossibile decodificare il corpo dell'email."

            emails.append({"from": from_, "subject": subject, "body": body.strip()})
        mail.logout()
        return emails
    except Exception as e:
        print(f"Errore generale durante la connessione IMAP o il fetch delle email: {e}")
        return []

# Per test manuale
if __name__ == "__main__":
    print("Tentativo di leggere le email non lette...")
    lista_email = fetch_unread_emails()
    if lista_email:
        for m in lista_email:
            print("\n--- NUOVA EMAIL ---")
            print(f"Da: {m['from']}")
            print(f"Oggetto: {m['subject']}")
            print(f"Corpo: {m['body'][:200]}...") # Stampa solo i primi 200 caratteri del corpo
    else:
        print("Nessuna email non letta trovata o errore durante il fetch.")

