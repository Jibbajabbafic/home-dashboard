// Update clock
function updateClock() {
    const now = new Date();
    document.getElementById('clock').textContent = now.toTimeString().split(' ')[0];
}
setInterval(updateClock, 1000);
updateClock();

// Parse times and update countdowns
function parseTime(timeStr) {
    if (!timeStr) return null;
    const parts = timeStr.trim().split(':');
    if (parts.length < 2) return null;
    const hours = parseInt(parts[0], 10);
    const minutes = parseInt(parts[1], 10);
    if (isNaN(hours) || isNaN(minutes)) return null;
    const now = new Date();
    const target = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hours, minutes);
    if (target < now) {
        target.setDate(target.getDate() + 1);
    }
    return target;
}

function getNextTramTime() {
    const times = [...document.querySelectorAll('.container:first-of-type ul li')]
        .map(li => li.textContent.trim().split(' ')[0])
        .filter(Boolean);
    const now = new Date();
    let nextTime = null;

    for (const time of times) {
        const tramTime = parseTime(time);
        if (!tramTime) continue;
        if (tramTime > now) {
            if (!nextTime || tramTime < nextTime) {
                nextTime = tramTime;
            }
        }
    }
    return nextTime;
}

function getNextFixtureTime() {
    const fixtures = Array.from(document.querySelectorAll('.container:nth-of-type(2) ul li'))
        .map(li => {
            // Try to parse date from the displayed text: dd/mm/yyyy at hh:mm
            const text = li.textContent || '';
            const match = text.match(/(\d{1,2}\/\d{1,2}\/\d{4}) at (\d{1,2}:\d{2})/);
            if (!match) return null;
            const [_, datePart, timePart] = match;
            const [day, month, year] = datePart.split('/').map(Number);
            const [hours, minutes] = timePart.split(':').map(Number);
            return new Date(year, month - 1, day, hours, minutes);
        })
        .filter(Boolean);

    const now = new Date();
    let nextTime = null;
    for (const fixtureTime of fixtures) {
        if (fixtureTime > now) {
            if (!nextTime || fixtureTime < nextTime) nextTime = fixtureTime;
        }
    }
    return nextTime;
}

function updateCountdowns() {
    const now = new Date();

    // Update tram countdown and remove passed times
    const listItems = document.querySelectorAll('.container:first-of-type ul li');
    listItems.forEach(item => {
        const text = item.textContent.trim();
        const time = text.split(' ')[0];
        const tramTime = parseTime(time);
        if (!tramTime) return;
        if (tramTime < now) {
            item.remove();
        } else {
            const minutesUntil = Math.floor((tramTime - now) / 60000);
            if (minutesUntil <= 15) {
                item.classList.add('imminent');
            } else {
                item.classList.remove('imminent');
            }
        }
    });

    // Highlight today's fixtures
    const fixtureItems = document.querySelectorAll('.container:nth-of-type(2) ul li');
    fixtureItems.forEach(item => {
        const text = item.textContent || '';
        const match = text.match(/(\d{1,2}\/\d{1,2}\/\d{4})/);
        if (!match) return;
        const [day, month, year] = match[0].split('/').map(Number);
        const fixtureDate = new Date(year, month - 1, day);
        if (fixtureDate.toDateString() === now.toDateString()) {
            item.classList.add('imminent');
        } else {
            item.classList.remove('imminent');
        }
    });

    // Update countdown for next tram
    const nextTram = getNextTramTime();
    if (nextTram) {
        const diffTram = Math.max(0, nextTram - now);
        const minutesTram = Math.floor(diffTram / 60000);
        const secondsTram = Math.floor((diffTram % 60000) / 1000);
        document.getElementById('nextTramCountdown').textContent =
            `Next tram in: ${minutesTram}m ${secondsTram}s`;
    } else {
        document.getElementById('nextTramCountdown').textContent = 'No upcoming trams';
    }

    // Update fixture countdown
    const nextFixture = getNextFixtureTime();
    if (nextFixture) {
        const diffFixture = Math.max(0, nextFixture - now);
        const daysFix = Math.floor(diffFixture / (1000 * 60 * 60 * 24));
        const hoursFix = Math.floor((diffFixture % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutesFix = Math.floor((diffFixture % (1000 * 60 * 60)) / (1000 * 60));
        document.getElementById('nextFixtureCountdown').textContent =
            `Next match in: ${daysFix}d ${hoursFix}h ${minutesFix}m`;
    }
}

// Initial update to prevent "calculating..." message
updateCountdowns();
// Then set up the interval for continuous updates
setInterval(updateCountdowns, 1000);
