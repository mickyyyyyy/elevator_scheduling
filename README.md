# Elevator Scheduling #

## Overview ##
Contains all the files needed to solve the problem of scheduling elevators for passengers on various floors in an elevator system.

![image](https://user-images.githubusercontent.com/62014208/190886524-641a3ece-bb3a-4038-9854-c8e98da2b871.png)

## Goals ##
The goal of this system is to schedule elevators to specific floors, this requires:  
  
    1. An accurate heuristic for the pickup time on a given floor for each elevator.  
    2. A traceable method for requesting pick ups from given floor.  
    3. A valid representation of the floors each elevator needs to visit, and the order in which they will be visiting them.  
    4. A succinct representation of the elevator system.  
    
In addition to many other sub-goals which stem from these major goals.

## Progress ##
The system currently has:  

    - [x] A pickup heuristic.  
    - [x] A string-based representation of the elevator system.  
    - [x] A traceable method for requests.  
    
## Future Additions ##
In terms of future additions, we aim to:  
  
    - [ ] Improve on the pickup heuristic.  
    - [ ] Utilise the pick up/drop off feature for improved tracing.  
    - [ ] Change the data structure used for the floors each elevator needs to travel to (aiming for a more efficient run-time).  
    - [ ] Utilise multiple threads or timers to incorporate elevators with various speeds in the same system.  
    - [ ] Improve the representation (using a GUI).  
