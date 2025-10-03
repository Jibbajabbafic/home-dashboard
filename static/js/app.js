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

// Remove an element with a swipe-away animation then remove from DOM.
function removeWithSwipe(el) {
    if (!el || el.__removing) return;
    el.__removing = true;

    // capture current height so we can animate height -> 0
    const height = el.getBoundingClientRect().height;
    el.style.height = `${height}px`;
    el.style.overflow = 'hidden';

    // Stop any ongoing 'imminent' animation to avoid transform conflicts
    el.classList.remove('imminent');
    // disable animations on the element (covers inline/stylesheet animations)
    el.style.animation = 'none';
    el.style.webkitAnimation = 'none';

    // small initial translate for a swiping effect, then collapse
    // use requestAnimationFrame to ensure styles are applied
    requestAnimationFrame(() => {
        el.classList.add('swipe-away');
        // force reflow
        // eslint-disable-next-line no-unused-expressions
        el.offsetHeight;
        el.classList.add('removing');
        el.style.height = '0px';
        el.style.paddingTop = '0px';
        el.style.paddingBottom = '0px';
        el.style.marginTop = '0px';
        el.style.marginBottom = '0px';
    });

    const onEnd = (ev) => {
        // wait for height transition or transform to finish
        if (ev.propertyName === 'height' || ev.propertyName === 'transform') {
            cleanup();
        }
    };

    function cleanup() {
        el.removeEventListener('transitionend', onEnd);
        if (el.parentNode) el.parentNode.removeChild(el);
    }

    el.addEventListener('transitionend', onEnd);
    // Fallback in case transitionend doesn't fire
    setTimeout(() => { if (el.parentNode) cleanup(); }, 800);
}

function getNextTransitTime() {
    const times = Array.from(document.querySelectorAll('#transitContainer ul li'))
        .map(li => li.textContent.trim().split(' ')[0])
        .filter(Boolean);
    const now = new Date();
    let nextTime = null;
    for (const time of times) {
        const serviceTime = parseTime(time, true); // roll to next day if needed
        if (!serviceTime) continue;
        if (serviceTime > now && (!nextTime || serviceTime < nextTime)) nextTime = serviceTime;
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

// Return a fixture Date that is either currently ongoing/finishing (kickoff -> +2.5h)
// or the next future fixture. This lets the countdown show 'ongoing'/'finishing'
// for matches that have already kicked off.
function getRelevantFixtureTime() {
    const fixtures = Array.from(document.querySelectorAll('.container:nth-of-type(2) ul li'))
        .map(li => parseFixtureFromText(li.textContent || ''))
        .filter(Boolean)
        .sort((a, b) => a - b);
    const now = new Date();

    // Prefer a fixture where now is between kickoff and kickoff + 2.5h
    for (const f of fixtures) {
        const end = new Date(f.getTime() + (2.5 * 60 * 60 * 1000));
        if (now >= f && now < end) return f;
    }

    // Otherwise return the next future fixture
    for (const f of fixtures) {
        if (f > now) return f;
    }

    return null;
}

// Parse bin collection list and return parsed items + the next upcoming collection
function getNextBinCollection() {
    const now = new Date();
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    const binNodes = Array.from(document.querySelectorAll('#binList .bin-item'));
    const items = binNodes.map(li => {
        const dateEl = li.querySelector('.item-date');
        const badgeEl = li.querySelector('.bin-badge');
        if (!dateEl) return null;
        const dateText = (dateEl.textContent || '').trim();
        const typeText = (badgeEl && badgeEl.textContent) ? badgeEl.textContent.trim() : '';
        const date = parseBinDateFromText(dateText);
        if (!date) return null;
        return { el: li, date, type: typeText };
    }).filter(Boolean);

    // Remove past bin items (dates before today)
    items.forEach(b => {
        if (b.date < startOfToday) {
            removeWithSwipe(b.el);
        }
    });

    let next = null;
    for (const item of items) {
        if (item.date >= startOfToday) {
            if (!next || item.date < next.date) next = item;
        }
    }

    return next;
}

function updateCountdowns() {
    const now = new Date();

    // Update transit countdown and remove passed times
    // Cache selectors
    const transitItems = document.querySelectorAll('#transitContainer ul li');
    transitItems.forEach(item => {
        const text = item.textContent.trim();
        const time = text.split(' ')[0];
        // Use rolled time so a service at e.g. 00:10 after midnight is considered next day
        const transitTime = parseTime(time, true);
        if (!transitTime) return;
        // If the transit time (possibly rolled to tomorrow) is already past, remove it
        if (transitTime <= now) {
            removeWithSwipe(item);
            return;
        }
        const minutesUntil = Math.floor((transitTime - now) / 60000);
        if (minutesUntil <= 15) item.classList.add('imminent');
        else item.classList.remove('imminent');
    });

    // Highlight fixtures in a window starting 1 hour before kick-off
    // until 2.5 hours after kick-off. Only remove fixtures after that window.
    const fixtureItems = document.querySelectorAll('.container:nth-of-type(2) ul li');
    fixtureItems.forEach(item => {
        const fixtureDate = parseFixtureFromText(item.textContent || '');
        if (!fixtureDate) return;

        // Define highlight window: start = kickOff - 1 hour, end = kickOff + 2.5 hours
        const windowStart = new Date(fixtureDate.getTime() - (60 * 60 * 1000));
        const windowEnd = new Date(fixtureDate.getTime() + (2.5 * 60 * 60 * 1000));

        // If we're past the entire window, remove the item
        if (now > windowEnd) {
            removeWithSwipe(item);
            return;
        }

        // Apply yellow 'imminent' for fixtures occurring today
        if (fixtureDate.toDateString() === now.toDateString()) {
            item.classList.add('imminent');
        } else {
            item.classList.remove('imminent');
        }

        // If the match is ongoing, add a red alert class
        if (now >= windowStart && now <= windowEnd) {
            item.classList.add('alert');
        } else {
            item.classList.remove('alert');
        }
    });

    // Update countdown for next transit (tram or bus)
    const nextTransit = getNextTransitTime();
    const transitLabelEl = document.getElementById('nextTransitCountdown');
    // derive readable noun from container data attribute
    const transitContainer = document.getElementById('transitContainer');
    const mode = transitContainer ? transitContainer.getAttribute('data-transit-mode') : 'tram';
    const noun = mode === 'bus' ? 'bus' : 'tram';
    if (nextTransit) {
        const diffTram = Math.max(0, nextTransit - now);
        const minutesTram = Math.floor(diffTram / 60000);
        const secondsTram = Math.floor((diffTram % 60000) / 1000);
        transitLabelEl.textContent = `Next ${noun} in: ${minutesTram}m ${secondsTram}s`;
    } else {
        transitLabelEl.textContent = `No upcoming ${noun}s`;
    }

    // Update fixture countdown
    const nextFixture = getRelevantFixtureTime();
    if (nextFixture) {
        // Windows:
        // ongoing: kick-off -> kick-off + 2h
        // finishing: kick-off + 2h -> kick-off + 2.5h
        // removal: after kick-off + 2.5h
        const kickoff = new Date(nextFixture.getTime());
        const ongoingEnd = new Date(kickoff.getTime() + (2 * 60 * 60 * 1000));
        const finishingEnd = new Date(kickoff.getTime() + (2.5 * 60 * 60 * 1000));

        if (now >= kickoff && now < ongoingEnd) {
            // Match ongoing
            const remaining = Math.max(0, ongoingEnd - now);
            const hoursLeft = Math.floor(remaining / (1000 * 60 * 60));
            const minutesLeft = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));
            document.getElementById('nextFixtureCountdown').textContent =
                `Match ongoing — ${hoursLeft}h ${minutesLeft}m left`;
        } else if (now >= ongoingEnd && now < finishingEnd) {
            // Match finishing window
            const remaining = Math.max(0, finishingEnd - now);
            const minutesLeft = Math.ceil(remaining / (1000 * 60));
            document.getElementById('nextFixtureCountdown').textContent =
                `Match finishing — ${minutesLeft}m left`;
        } else if (now >= finishingEnd) {
            // Past finishing window: nothing to show here (items are removed elsewhere)
            document.getElementById('nextFixtureCountdown').textContent = 'No ongoing match';
        } else {
            const diffFixture = Math.max(0, nextFixture - now);
            const daysFix = Math.floor(diffFixture / (1000 * 60 * 60 * 24));
            const hoursFix = Math.floor((diffFixture % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutesFix = Math.floor((diffFixture % (1000 * 60 * 60)) / (1000 * 60));
            document.getElementById('nextFixtureCountdown').textContent =
                `Next match in: ${daysFix}d ${hoursFix}h ${minutesFix}m`;
        }
    }

    // Update bin collections (delegated to helper)
    const nextBin = getNextBinCollection();
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

        // Only highlight bin items if they are today or tomorrow
        document.querySelectorAll('#binList .bin-item').forEach(el => {
            el.classList.remove('next', 'imminent');
        });

        if (!nextBin.el.__removing) {
            const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            const startOfDayAfterTomorrow = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 2);

            // Add imminent class only if the bin collection is today or tomorrow
            if (nextBin.date >= startOfToday && nextBin.date < startOfDayAfterTomorrow) {
                nextBin.el.classList.add('imminent');
            }
        }
    } else {
        document.getElementById('nextBinCountdown').textContent = 'No upcoming bin collections';
    }
}

// Debug helpers
function gatherDebugInfo() {
    const now = new Date();
    const tramTimes = Array.from(document.querySelectorAll('#transitContainer ul li'))
        .map(li => li.textContent.trim().split(' ')[0]).filter(Boolean);

    const fixtures = Array.from(document.querySelectorAll('.container:nth-of-type(2) ul li'))
        .map(li => ({ text: li.textContent.trim(), parsed: parseFixtureFromText(li.textContent || '') }));

    const bins = Array.from(document.querySelectorAll('#binList .bin-item'))
        .map(li => ({ text: (li.querySelector('.item-date') || {}).textContent, badge: (li.querySelector('.bin-badge') || {}).textContent }));

    const relevant = getRelevantFixtureTime();

    return { now, tramTimes, fixtures, bins, relevant };
}

function renderDebugPanel() {
    const panel = document.getElementById('debugPanel');
    const content = document.getElementById('debugContent');
    if (!panel || !content) return;
    const info = gatherDebugInfo();
    let html = '';
    html += `<div><strong>Now:</strong> ${info.now.toString()}</div>`;
    html += `<div style="margin-top:6px"><strong>Transit times:</strong><pre>${JSON.stringify(info.tramTimes, null, 2)}</pre></div>`;
    html += `<div style="margin-top:6px"><strong>Fixtures (text / parsed):</strong><pre>${info.fixtures.map(f => f.text + ' => ' + (f.parsed ? f.parsed.toString() : 'null')).join('\n')}</pre></div>`;
    html += `<div style="margin-top:6px"><strong>Relevant fixture:</strong> ${info.relevant ? info.relevant.toString() : 'null'}</div>`;
    html += `<div style="margin-top:6px"><strong>Bins:</strong><pre>${JSON.stringify(info.bins, null, 2)}</pre></div>`;
    content.innerHTML = html;
}

// Wire up debug buttons
document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('dbgBtn');
    const panel = document.getElementById('debugPanel');
    const logBtn = document.getElementById('dbgLog');
    if (btn && panel) {
        btn.addEventListener('click', () => {
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
            renderDebugPanel();
        });
    }
    if (logBtn) {
        logBtn.addEventListener('click', () => console.log('Debug', gatherDebugInfo()));
    }
});

// Also refresh debug panel on every countdown update
const _oldUpdate = updateCountdowns;
updateCountdowns = function () {
    _oldUpdate();
    renderDebugPanel();
};

// Initial update to prevent "calculating..." message
updateCountdowns();
// Then set up the interval for continuous updates
setInterval(updateCountdowns, 1000);
