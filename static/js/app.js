// Update clock
function updateClock() {
    const now = new Date();
    document.getElementById('clock').textContent = now.toTimeString().split(' ')[0];
}
setInterval(updateClock, 1000);
updateClock();

// Parse a time string "HH:MM" into a Date for today. If rollIfPast is true,
// roll the date to tomorrow when the parsed time is earlier than now.
function parseTime(timeStr, rollIfPast = true) {
    if (!timeStr) return null;
    const parts = timeStr.trim().split(':');
    if (parts.length < 2) return null;
    const hours = parseInt(parts[0], 10);
    const minutes = parseInt(parts[1], 10);
    if (isNaN(hours) || isNaN(minutes)) return null;
    const now = new Date();
    const target = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hours, minutes, 0, 0);
    if (rollIfPast && target < now) {
        target.setDate(target.getDate() + 1);
    }
    return target;
}

// Parse a fixture li's text for a Date in the format dd/mm/yyyy at hh:mm
function parseFixtureFromText(text) {
    const match = (text || '').match(/(\d{1,2}\/\d{1,2}\/\d{4}) at (\d{1,2}:\d{2})/);
    if (!match) return null;
    const [, datePart, timePart] = match;
    const [day, month, year] = datePart.split('/').map(Number);
    const [hours, minutes] = timePart.split(':').map(Number);
    if ([day, month, year, hours, minutes].some(n => Number.isNaN(n))) return null;
    return new Date(year, month - 1, day, hours, minutes);
}

// Parse a bin date string from display formats: DD/MM/YYYY or YYYY-MM-DD
function parseBinDateFromText(dateText) {
    if (!dateText) return null;
    const dm = dateText.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})/);
    if (dm) {
        const d = Number(dm[1]);
        const m = Number(dm[2]);
        const y = Number(dm[3]);
        return new Date(y, m - 1, d, 23, 59, 59, 999);
    }
    const iso = dateText.match(/(\d{4})-(\d{1,2})-(\d{1,2})/);
    if (iso) {
        const y = Number(iso[1]);
        const m = Number(iso[2]);
        const d = Number(iso[3]);
        return new Date(y, m - 1, d, 23, 59, 59, 999);
    }
    return null;
}

function getNextTramTime() {
    const times = Array.from(document.querySelectorAll('.container:first-of-type ul li'))
        .map(li => li.textContent.trim().split(' ')[0])
        .filter(Boolean);
    const now = new Date();
    let nextTime = null;
    for (const time of times) {
        const tramTime = parseTime(time, true); // roll to next day if needed
        if (!tramTime) continue;
        if (tramTime > now && (!nextTime || tramTime < nextTime)) nextTime = tramTime;
    }
    return nextTime;
}

function getNextFixtureTime() {
    const fixtures = Array.from(document.querySelectorAll('.container:nth-of-type(2) ul li'))
        .map(li => parseFixtureFromText(li.textContent || ''))
        .filter(Boolean);
    const now = new Date();
    let nextTime = null;
    for (const fixtureTime of fixtures) {
        if (fixtureTime > now && (!nextTime || fixtureTime < nextTime)) nextTime = fixtureTime;
    }
    return nextTime;
}

function updateCountdowns() {
    const now = new Date();

    // Update tram countdown and remove passed times
    // Cache selectors
    const tramItems = document.querySelectorAll('.container:first-of-type ul li');
    tramItems.forEach(item => {
        const text = item.textContent.trim();
        const time = text.split(' ')[0];
        const tramTimeToday = parseTime(time, false); // don't roll -- used to decide removal
        if (!tramTimeToday) return;
        if (tramTimeToday <= now) {
            item.remove();
            return;
        }
        const minutesUntil = Math.floor((tramTimeToday - now) / 60000);
        if (minutesUntil <= 15) item.classList.add('imminent');
        else item.classList.remove('imminent');
    });

    // Highlight today's fixtures
    const fixtureItems = document.querySelectorAll('.container:nth-of-type(2) ul li');
    fixtureItems.forEach(item => {
        const fixtureDate = parseFixtureFromText(item.textContent || '');
        if (!fixtureDate) return;
        if (fixtureDate.toDateString() === now.toDateString()) item.classList.add('imminent');
        else item.classList.remove('imminent');
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

    // Update bin collections
    const binNodes = Array.from(document.querySelectorAll('#binList .bin-item'));
    const binItems = binNodes.map(li => {
        const dateEl = li.querySelector('.item-date');
        const badgeEl = li.querySelector('.bin-badge');
        if (!dateEl) return null;
        const dateText = (dateEl.textContent || '').trim();
        const typeText = (badgeEl && badgeEl.textContent) ? badgeEl.textContent.trim() : '';
        const date = parseBinDateFromText(dateText);
        if (!date) return null;
        return { el: li, date, type: typeText };
    }).filter(Boolean);

    let nextBin = null;
    for (const item of binItems) {
        if (item.date >= new Date(now.getFullYear(), now.getMonth(), now.getDate())) {
            if (!nextBin || item.date < nextBin.date) nextBin = item;
        }
    }

    if (nextBin) {
        // Show simplified countdown: Today / Tomorrow / X days
        const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const startOfTomorrow = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
        const startOfNext = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 2);

        let label = '';
        if (nextBin.date >= startOfToday && nextBin.date < startOfTomorrow) {
            label = 'Today';
        } else if (nextBin.date >= startOfTomorrow && nextBin.date < startOfNext) {
            label = 'Tomorrow';
        } else {
            const diffDays = Math.ceil((nextBin.date - startOfToday) / (1000 * 60 * 60 * 24));
            label = `${diffDays} days`;
        }

        document.getElementById('nextBinCountdown').textContent = `Next bin: ${label}`;

        // Highlight bin items that are imminent (within 24 hours)
        document.querySelectorAll('#binList .bin-item').forEach(el => el.classList.remove('next'));
        nextBin.el.classList.add('imminent');
    } else {
        document.getElementById('nextBinCountdown').textContent = 'No upcoming bin collections';
    }
}

// Initial update to prevent "calculating..." message
updateCountdowns();
// Then set up the interval for continuous updates
setInterval(updateCountdowns, 1000);
