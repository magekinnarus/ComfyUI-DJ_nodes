import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "DJ.PromptPresets",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "DJ_PromptPresets") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                const minWidth = 400;
                // UPDATED HEIGHTS: 100px and 50px
                const posHeight = 100;
                const negHeight = 50;
                const gap = 30;

                const setupOutputWidget = (wName, height, label) => {
                    const w = this.widgets?.find((w) => w.name === wName);
                    if (!w) return;

                    w.type = "customtext";
                    w.computeSize = () => [minWidth, height + gap];

                    if (w.inputEl) {
                        w.inputEl.readOnly = true;
                        w.inputEl.placeholder = label;
                        w.inputEl.style.display = "block";
                        w.inputEl.style.minWidth = "200px";
                        w.inputEl.style.minHeight = `${height}px`;
                        w.inputEl.style.marginTop = "5px";
                        w.inputEl.style.marginBottom = "5px";
                        w.inputEl.style.backgroundColor = "#222"; // Darker background for read-only
                        w.inputEl.style.color = "#aaa";
                    }
                    return w;
                };

                // Setup Output Widgets
                // We add them in order. If they exist, they are found.
                setupOutputWidget("generated_positive", posHeight, "Generated Positive Prompt (Runs on Queue)");
                setupOutputWidget("generated_negative", negHeight, "Generated Negative Prompt (Runs on Queue)");

                // Force initial resize
                requestAnimationFrame(() => {
                    const computed = this.computeSize();
                    this.setSize([Math.max(computed[0], minWidth), computed[1] + 20]);
                    this.setDirtyCanvas(true, true);
                });

                return r;
            };

            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);

                if (message?.generated_positive) {
                    const w = this.widgets?.find((w) => w.name === "generated_positive");
                    if (w) w.value = message.generated_positive[0];
                }
                if (message?.generated_negative) {
                    const w = this.widgets?.find((w) => w.name === "generated_negative");
                    if (w) w.value = message.generated_negative[0];
                }
            };

            // Re-apply styles on configure (reload)
            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function () {
                if (onConfigure) onConfigure.apply(this, arguments);
                requestAnimationFrame(() => {
                    const posHeight = 100; // Updated height
                    const negHeight = 50;  // Updated height
                    const minWidth = 400;
                    const gap = 30;

                    const setupStyle = (wName, height) => {
                        const w = this.widgets?.find((w) => w.name === wName);
                        if (w && w.inputEl) {
                            w.computeSize = () => [minWidth, height + gap];
                            w.inputEl.style.display = "block";
                            w.inputEl.style.minWidth = "200px";
                            w.inputEl.style.minHeight = `${height}px`;
                            w.inputEl.style.marginTop = "5px";
                            w.inputEl.style.marginBottom = "5px";
                            w.inputEl.style.backgroundColor = "#222";
                            w.inputEl.style.color = "#aaa";
                        }
                    };
                    setupStyle("generated_positive", posHeight);
                    setupStyle("generated_negative", negHeight);

                    // Force resize
                    const computed = this.computeSize();
                    this.setSize([Math.max(computed[0], minWidth), computed[1] + 20]);
                    this.setDirtyCanvas(true, true);
                });
            };

            console.log("DJ_PromptPresets Layout Loaded: Heights 100/50");
        }
    },
});
