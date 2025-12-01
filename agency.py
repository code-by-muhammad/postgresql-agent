from dotenv import load_dotenv
from agency_swarm import Agency

from postgresql_agent import create_postgresql_agent

import asyncio

load_dotenv()

# do not remove this method, it is used in the main.py file to deploy the agency (it has to be a method)
def create_agency(load_threads_callback=None):
    postgresql_agent = create_postgresql_agent()
    agency = Agency(
        postgresql_agent,
        name="PostgreSQLAgency",
        load_threads_callback=load_threads_callback,
    )
    return agency
if __name__ == "__main__":
    agency = create_agency()
    # test 1 message
    # async def main():
    #     response = await agency.get_response("Hello, how are you?")
    #     print(response)
    # asyncio.run(main())

    # run in terminal
    agency.terminal_demo()