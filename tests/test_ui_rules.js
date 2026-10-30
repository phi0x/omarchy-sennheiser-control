const fs = require('fs');
const vm = require('vm');
const assert = require('assert/strict');
const source = fs.readFileSync(require('path').join(__dirname, '../UiRules.js'), 'utf8').replace('.pragma library', '');
const rules = vm.createContext({});
vm.runInContext(source, rules);
for (const mode of [0,1,2,4]) {
    assert.equal(rules.dependency('bass_boost', {audio_mode:mode}).available, mode === 1);
    assert.equal(rules.dependency('crossfeed', {audio_mode:mode}).available, true);
}
for (const key of ['smart_pause','auto_answer','auto_off']) {
    assert.equal(rules.dependency(key, {on_head:0}).available,false);
    assert.equal(rules.dependency(key, {on_head:1}).available,true);
}
for (const key of ['adaptive','comfort','anti_wind']) {
    assert.equal(rules.dependency(key, {anc:0}).available,false);
    assert.equal(rules.dependency(key, {anc:1}).available,true);
}
assert.match(rules.eqStatus(1,1), /^Active/);
assert.match(rules.eqStatus(1,4), /^Inactive/);
assert.match(rules.eqStatus(4,1), /^Inactive/);
assert.match(rules.eqStatus(4,4), /^Active/);
assert.match(rules.eqStatus(2,4), /Speech/);
assert.match(rules.eqStatus(0,4), /off/);
console.log('UI dependency and EQ-mode checks passed');
