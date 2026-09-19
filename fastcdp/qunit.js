async tests => {
    window.QUnit = {config: {autostart: false}};
    await new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://code.jquery.com/qunit/qunit-2.26.0.js';
        script.onload = resolve;
        script.onerror = () => reject(new Error('Could not load QUnit'));
        document.head.append(script);
    });

    const failures = [];
    const done = new Promise(resolve => {
        QUnit.on('testEnd', test => {
            if (test.status === 'failed') failures.push({
                name: test.fullName,
                errors: test.errors.map(({message, stack}) => ({message, stack}))
            });
        });
        QUnit.on('runEnd', ({status, testCounts}) => resolve({status, testCounts, failures}));
    });

    new Function(tests)();
    QUnit.start();
    return done;
}
