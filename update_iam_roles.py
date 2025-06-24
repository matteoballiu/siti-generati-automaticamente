from google.cloud import resourcemanager_v3 # Assicurati che sia la versione v3

# Sostituisci con l'ID esatto del tuo progetto Google Cloud
YOUR_PROJECT_ID = "sito-automazione-aziende" 
# Sostituisci con l'email esatta del tuo account di servizio Cloud Build
CLOUDBUILD_SERVICE_ACCOUNT_EMAIL = "358125195620@cloudbuild.gserviceaccount.com"

# Ruoli che devono essere concessi all'account di servizio Cloud Build
ROLES_TO_GRANT = [
    "roles/secretmanager.secretAccessor",
    "roles/pubsub.subscriber",
    "roles/source.reader",
    # Puoi aggiungere altri ruoli qui se necessario in futuro
]

def update_cloudbuild_service_account_roles():
    """
    Aggiorna i ruoli per l'account di servizio Cloud Build.
    """
    client = resourcemanager_v3.ProjectsClient() # Usa il client v3 esplicitamente
    
    try:
        # 1. Ottieni la policy IAM attuale del progetto
        # Passa il project ID come parte del resource name "projects/YOUR_PROJECT_ID"
        policy = client.get_iam_policy(resource=f"projects/{YOUR_PROJECT_ID}")
        print(f"Policy IAM attuale per il progetto {YOUR_PROJECT_ID} ottenuta.")
        
        # Converte l'email dell'account di servizio nel formato membro IAM
        member_id = f"serviceAccount:{CLOUDBUILD_SERVICE_ACCOUNT_EMAIL}"
        
        roles_added_count = 0
        
        # 2. Per ogni ruolo da concedere
        for role_to_grant in ROLES_TO_GRANT:
            role_exists_for_member = False
            
            # Cerca se il membro ha già questo ruolo
            for binding in policy.bindings:
                if binding.role == role_to_grant and member_id in binding.members:
                    role_exists_for_member = True
                    break
            
            if role_exists_for_member:
                print(f"Il ruolo '{role_to_grant}' è già presente per {CLOUDBUILD_SERVICE_ACCOUNT_EMAIL}.")
            else:
                # Se il ruolo non è presente, aggiungilo
                # Controlla se esiste già un binding per quel ruolo
                binding_found = False
                for binding in policy.bindings:
                    if binding.role == role_to_grant:
                        binding.members.append(member_id)
                        binding_found = True
                        break
                
                if not binding_found:
                    # Se non esiste nessun binding per questo ruolo, creane uno nuovo
                    new_binding = resourcemanager_v3.types.Policy.Binding(role=role_to_grant, members=[member_id]) # Specifica il tipo di Binding
                    policy.bindings.append(new_binding)
                    
                print(f"Aggiunto il ruolo '{role_to_grant}' a {CLOUDBUILD_SERVICE_ACCOUNT_EMAIL}.")
                roles_added_count += 1
                
        if roles_added_count == 0:
            print("Nessun nuovo ruolo da aggiungere o tutti i ruoli erano già presenti.")
            return

        # 3. Imposta la policy IAM aggiornata sul progetto
        # Anche qui, passa il project ID come resource name e la policy aggiornata
        updated_policy = client.set_iam_policy(resource=f"projects/{YOUR_PROJECT_ID}", policy=policy)
        print(f"Policy IAM aggiornata con successo per il progetto {YOUR_PROJECT_ID}.")
        
    except Exception as e:
        print(f"ERRORE durante l'aggiornamento dei ruoli IAM: {e}")
        print("Assicurati che l'account autenticato nella gcloud CLI abbia il ruolo 'Amministratore IAM progetto' o 'Editor'.")

if __name__ == "__main__":
    print("Tentativo di aggiornare i ruoli per l'account di servizio Cloud Build...")
    update_cloudbuild_service_account_roles()