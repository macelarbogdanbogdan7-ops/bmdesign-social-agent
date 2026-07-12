"""
Script de DEMO pentru App Review (nu face parte din automatizarea normala).

Demonstreaza capacitatea reala de a scrie comentarii si a raspunde, care
functioneaza deja (spre deosebire de citirea comentariilor/mesajelor de la
alti utilizatori, care necesita Advanced Access de la Meta).

Ce face:
1. Posteaza un comentariu de test pe cea mai recenta postare (simuland un
   comentariu de client, pentru scopul demo-ului).
2. Raspunde imediat la acel comentariu, folosind acelasi mecanism pe care
   agentul il va folosi automat dupa aprobarea App Review.

Ruleaza o singura data, manual, doar pentru inregistrarea video.
"""
import instagram_publisher as ig

DEMO_COMMENT_TEXT = "Vreau si eu o bucatarie ca asta, cat ar costa un proiect similar?"
DEMO_REPLY_TEXT = "Multumim pentru interes! Iti trimit acum un mesaj cu detalii."

if __name__ == "__main__":
    media_list = ig.list_recent_media(limit=1)
    if not media_list:
        raise RuntimeError("Nu am gasit nicio postare recenta.")

    media_id = media_list[0]["id"]
    print(f"Postare folosita pentru demo: {media_id}")

    comment_id = ig.post_comment(media_id, DEMO_COMMENT_TEXT)
    print(f"Comentariu demo postat: {comment_id}")

    reply_id = ig.reply_to_comment(comment_id, DEMO_REPLY_TEXT)
    print(f"Raspuns postat cu succes: {reply_id}")
