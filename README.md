# Problem Statement
This project aims to develop a web-based itinerary planning system capable of generating optimal travel routes across a simplified flight network. The application will allow users to input a customized set of destinations and will compute the most efficient sequence in which to visit them, based on factors such as total travel distance, number of flights, or overall travel time (depending on the optimization criteria selected).

To provide a focused and contextually relevant experience, the system will limit all trip origins to three major airports serving the Los Angeles and Orange County regions: Los Angeles International Airport (LAX), Long Beach Airport (LGB), and John Wayne Airport (SNA). By tailoring the platform to these specific departure points, the project aligns the itinerary planner with the travel habits and needs of residents in Southern California, while also narrowing the problem scope to a manageable and well-defined portion of a larger flight network.

# Set Up
## Setting up Back End
In the repository file:

1. (OPTIONAL) create a virtual environment (used name: venv) then activate it
### On Windows
``` python3 -m venv <environment name> ```
``` <environment name>/Scripts/Activate ```
2. pip install the dependency files
``` pip install -r requirements.txt ```
3. Run the backend server
``` cd .. ```
``` uvicorn backend.api:app --reload --port 8000 ```

## Setting up Front End
Use another terminal on the repository file:

1. Install npm v10.9.3 / pnpm 
2. Download all the dependencies
``` npm install ```
3. Run the server
``` npm run dev ```

