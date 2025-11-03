let index = 0;
let startTime = 0;

function startStudy(trials, worker_id, condition, completion_code) {

    loadTrial();

    function loadTrial() {
        // ✅ Finished all trials → redirect to completion page with code
        if (index >= trials.length) {
            alert("Task complete! Your completion code is: " + completion_code);
            window.location.href = "/complete?completion_code=" + completion_code;
            return;
        }

        const t = trials[index];
        startTime = performance.now();

        document.getElementById("task").innerHTML = `
            <h3>Article ${index + 1} of ${trials.length}</h3>
            <b>Headline:</b> ${t.title}<br>
            <b>Description:</b> ${t.text}<br>
            <b>Date:</b> ${t.date}<br><br>

            <button id="realBtn">Real</button>
            <button id="fakeBtn">Fake</button>
            <br><br>

            Confidence (0 = guess, 100 = certain):
            <input type="number" id="conf" min="0" max="100" value="50"><br><br>

            ${condition === "assisted" ? '<button id="aiBtn">Get AI Suggestion</button>' : ''}
            <p id="ai_output"></p>
        `;

        // ✅ AI button handler (assisted condition only)
        if (condition === "assisted") {
            document.getElementById("aiBtn").onclick = () => {
                fetch("/predict", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ title: t.title, text: t.text })
                })
                .then(res => res.json())
                .then(data => {
                    window.ai_label = data.label;
                    window.ai_conf = data.confidence;
                    document.getElementById("ai_output").innerHTML =
                        `<b>AI Suggestion:</b> ${data.label} (${data.confidence}%)`;
                });
            };
        }

        // ✅ Real / Fake decision handlers
        document.getElementById("realBtn").onclick = () => submitResponse("REAL");
        document.getElementById("fakeBtn").onclick = () => submitResponse("FAKE");

        function submitResponse(label) {
            const endTime = performance.now();
            const response_time = Math.round(endTime - startTime);
            const confidence = document.getElementById("conf").value;

            const truth = String(t.label).toLowerCase();
            const isCorrect =
                (label === 'REAL' && truth === 'true') ||
                (label === 'FAKE' && truth !== 'true');

            // ✅ Disable buttons AFTER answer
            document.getElementById("realBtn").disabled = true;
            document.getElementById("fakeBtn").disabled = true;
            if (condition === "assisted" && document.getElementById("aiBtn"))
                document.getElementById("aiBtn").disabled = true;

            // ✅ Show feedback and next button
            document.getElementById("task").innerHTML += `
                <p style="font-weight:bold; color:${isCorrect ? 'green' : 'red'};">
                    ${isCorrect ? "Correct!" : `Incorrect — It was actually ${truth.toUpperCase()}`}
                </p>
                <button id="nextBtn">Next</button>
            `;

            // ✅ Build payload including completion_code
            const payload = {
                worker_id: worker_id,
                completion_code: completion_code,
                condition: condition,

                trial_id: index,
                title: t.title,
                text: t.text,
                date: t.date,
                ground_truth: t.label,
                human_label: label,

                ai_label: window.ai_label || null,
                ai_confidence: window.ai_conf || null,

                response_time: response_time,
                confidence_rating: confidence
            };

            // ✅ Save to server
            fetch("/submit_trial", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });

            // ✅ Move to next trial only when button clicked
            document.getElementById("nextBtn").onclick = () => {
                window.ai_label = null;
                window.ai_conf = null;
                index++;
                loadTrial();
            };
        }
    }
}
