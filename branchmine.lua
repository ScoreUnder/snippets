-- Branch miner
-- By Score_Under of course

paused = false
running = true

function mineAndGo()
    if not running then error("Quitting") end
    while paused do coroutine.yield() end
    while not refuelIfNeeded() do
        print("Pausing because out of fuel")
        paused = true
        while paused do coroutine.yield() end
    end
    local attempts = 10
    while attempts > 0 and not turtle.forward() do
        turtle.dig()
        attempts = attempts - 1
    end
    turtle.digUp()
end

function refuelIfNeeded()
    local fuel = turtle.getFuelLevel()
    if fuel > 0 or fuel == "unlimited" then
        return true
    end
    return forceRefuel()
end

function forceRefuel()
    print("Refuelling")
    for slot = 1, 16 do
        turtle.select(slot)
        if turtle.refuel() then
            print("Success")
            return true
        end
    end
    return false
end

function mineArm()
    for pos = 1, 8 do mineAndGo() end
    turtle.turnLeft()
    turtle.turnLeft()
    for pos = 1, 8 do mineAndGo() end
end

function mineArms()
    turtle.turnLeft()
    for arms = 1, 2 do mineArm() end
    turtle.turnRight()
end

function mineLoop()
    while running do
        mineArms()
        for gap = 1, 3 do mineAndGo() end
    end
end

function commandProcessor()
    while running do
        local event, char = os.pullEvent("char")
        if char == "p" then
            paused = not paused
        elseif char == "q" then
            running = false
            paused = false
        elseif char == "r" then
            forceRefuel()
        elseif char == "s" then
            print("STATUS REPORT")
            print("Fuel: " .. turtle.getFuelLevel())
            print("Paused: " .. tostring(paused))
            print("ur a faget: true")
        end
    end
end

parallel.waitForAll(mineLoop, commandProcessor)
