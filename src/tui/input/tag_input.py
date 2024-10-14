from src.shared.models.tag import Tag
from src.shared.repositories.tag_repository import SqliteTagRepository


def ask_input() -> str:
    while True:
        try:
            tag_input = input("\tEnter a tag. > ")
            if int(tag_input):
                print("\tTag must be a string.")
        except ValueError :
            return tag_input.strip()


def get_tag_id_from_input(tag_repo : SqliteTagRepository, tag : str) -> int | None:
    while True :
        try :
            return tag_repo.return_tag_id_if_exists(tag)
        except TypeError:
            add_tag = input("\tThe tag doesn't exist. Do you want to add it ? (Y/N) > ")

            if add_tag.upper().strip().startswith("Y"):
                _, tag_guid = tag_repo.create(Tag(tag=tag))
                tag_id = tag_repo.get_id_from_guid(tag_guid)
                tag_repo.connexion.commit()
                return tag_id
            if add_tag.upper().strip().startswith("N"):
                tag = input("\tEnter your tag again : > ")
                if not tag:
                    return None
                continue
            else :
                print("\tEnter Y for Yes and N for No.")
