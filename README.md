# Problem Statement
This project aims to develop a web-based itinerary planning system capable of generating optimal travel routes across a simplified flight network. The application will allow users to input a customized set of destinations and will compute the most efficient sequence in which to visit them, based on factors such as total travel distance, number of flights, or overall travel time (depending on the optimization criteria selected).

To provide a focused and contextually relevant experience, the system will limit all trip origins to three major airports serving the Los Angeles and Orange County regions: Los Angeles International Airport (LAX), Long Beach Airport (LGB), and John Wayne Airport (SNA). By tailoring the platform to these specific departure points, the project aligns the itinerary planner with the travel habits and needs of residents in Southern California, while also narrowing the problem scope to a manageable and well-defined portion of a larger flight network.

# Setup (Ubuntu 24.04 LTS)

## Prerequisites
### Node.js and NPM
```bash
# Download and install nvm:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

# in lieu of restarting the shell
\. "$HOME/.nvm/nvm.sh"

# Download and install Node.js:
nvm install 25

# Verify the Node.js version:
node -v # Should print "v25.2.1".

# Verify npm version:
npm -v # Should print "11.6.2".
```

### Python
```bash
# Update package list
sudo apt update

# Install Python Prerequisites
sudo apt install -y python3 python3-venv python3-pip
```
## Setting up Back End
Open a terminal in the project root directory.

#### 1. Navigate to the Back End Directory
```bash
cd backend
```
#### 2. Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
With the virtual environment active, install the Python requirements:
```bash
pip install -r backend/requirements.txt
```

#### 4. Run the Backend Server
```bash
fastapi dev api.py 
```

## Setting up the Front End
#### 1. Navigate to the Front End Directory
```bash
cd frontend
```
#### 2. Install Dependencies
```bash
npm install
```

#### 3. Run the Frontend Server
```bash
npm run dev
```
The frontend application will typically run at http://localhost:5173 (check the terminal output for the exact URL).

# Setup (Windows)

## Setting up Backend
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

1. Go to the frontend file
``` cd frontend ```
2. Install npm v10.9.3 / pnpm 
3. Download all the dependencies
``` npm install ```
4. Run the server
``` npm run dev ```