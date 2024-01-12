from src.shared.models.tag import Tag
from src.shared.repositories.tag_repository import SqliteTagRepository


def ask_input() -> str:
    while True:
        try:
            tag_input = input("Enter a tag. > ")
            if int(tag_input):
                print("Tag must be a string.")
        except ValueError :
            print(tag_input)
            return tag_input.strip()


def get_tag_id_from_input(tag_repo : SqliteTagRepository, tag : str) :
    while True :

        try :
            return tag_repo.return_tag_id_if_exists(tag)
        except TypeError:
            add_tag = input("The tag doesn't exist. Do you want to add it ? (Y/N) > ")

            if add_tag.upper().strip() == "Y":
                _, tag_guid = tag_repo.create(Tag(tag=tag))
                tag_id = tag_repo.get_id_from_guid(tag_guid)
                tag_repo.connexion.commit()
                return tag_id
            if add_tag.upper().strip() == "N":
                tag = input("Enter your tag again : > ")
                continue
            else :
                print("Enter Y for Yes and N for No.")
