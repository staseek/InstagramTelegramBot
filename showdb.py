import config
import InstagramBotDAO


def main():
    session = config.Session()
    for x in session.query(InstagramBotDAO.Chat).all():
        print(x)

    print('''---------- subscriptions ------ ''')

    for x in session.query(InstagramBotDAO.InstagramSubscription).all():
        print(x)
    session.close()

if __name__ == "__main__":
    main()
