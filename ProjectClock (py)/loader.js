const child_process = require("child_process");
const fs = require("fs");

/**
 * Configure your multiple bots here...
 * 
 *      name: "Name of your Bot",
 *      dir: 'Directory Name',
 *      start_file: 'The file to Run',
 *      type: node || python3.9 || python3.10,
 *      auto_restart: If you want it to try to start backup after a crash
 *      max_retries: Maximum amount of times to try again after a crash if auto restarting
 * 
 * Each object in the array below is a new bot that will run.
 */
const bots = [
    {
        name: 'Arab Clock Bot',
        dir: 'ArabClockBot',
        start_file: 'index.js',
        type: 'node',
        auto_restart: true,
        max_retries: 2,
    },
    {
        name: 'Project Clock',
        dir: 'ProjectClock',
        start_file: 'main.py',
        type: 'python3.10',
        auto_restart: false,
    },
];

// Don't edit below this line unless you know what you are doing

const acceptedTypes = [ "node", "python3.9", "python3.10" ];

console.log(`[Loader]Loading ${bots.length} applications`);

function start(item) {
    return new Promise(async (resolve, reject) => {
        if(!acceptedTypes.includes(item.type)) reject("TYPE_NOT_SUPPORTED");
        console.log(`[Loader][${item.name}] => Starting { type: ${item.type}, dir: ${item.dir}, start_file: ${item.start_file}, auto_restart: ${item.auto_restart} }`);
        if(item.type === "node") await typeNode(item);
        if(item.type.includes("python")) await typePython(item);
        resolve(true);
    });
}

function run(item) {
    if(!item.auto_restart) item.auto_restart = false;
    if(!item.retries) item.retries = 0;
    if(!item.max_retries) item.max_retries = 2;
    item.retries++;
    return start(item).then(() => {
        console.log(`[Loader][${item.name}] => Exited... Auto-Restart: ${item.auto_restart}`);
        if(item.auto_restart && item.retries <= item.max_retries) {
            console.log(`[Loader][${item.name}] WARN => Auto-Restarting... Attempt ${item.retries}`);
            run(item);
        } else {
            console.log(`[Loader][${item.name}] ERROR => Too Many Attempts... Exiting.`);
        }
    }).catch((err) => {
        console.log(`[Loader][${item.name}] ERROR => Error Detected... ${err}`);
        if(item.retires <= 5 && item.auto-restart) run(item);
        console.log(`[Loader][${item.name}] ERROR => Too Many Attempts... Exiting.`);
    });
}

function typeNode(item) {
    return new Promise((resolve) => {
        console.log(`[Loader][${item.name}] NodeJS => Installing Dependencies...`);
        child_process.spawn("npm", [ "install", "--build-from-resource", "--no-bin-links", "--cache", "/tmp/.npm-global", "--update-notifier", "false", "--prefix", `/home/container/${item.dir}` ], {
            cwd: `./${item.dir}`
        }).on("exit", () => {
            console.log(`[Loader][${item.name}] NodeJS => Opening file ${item.start_file}`);

            child_process.spawn(process.execPath, [ item.start_file ], {
                cwd: `./${item.dir}`,
                stdio: 'inherit'
            }).on("exit", resolve);
        });
    });
}

function typePython(item) {
    return new Promise((resolve) => {
        console.log(`[Loader][${item.name}] Python => Installing Dependencies...`);
        let requirementsFile = "requirements.txt";
        if (fs.existsSync(requirementsFile)) console.log(`[Loader][${item.name}] Python => Found ${requirementsFile}`);
        else {
            console.log(`[Loader][${item.name}] Python => No ${requirementsFile} found - generating...`);
            fs.writeFileSync(requirementsFile, "");
        }
        const requirements = fs.readFileSync(requirementsFile, "utf-8");
        for(let req of requirements.split("\n")) {
            if(!req) continue;
            if (["random", "math", "os", "subprocess", "datetime", "shutil", "time"].includes(req)) {
                console.log(`[Loader][${item.name}] Python => Not installing ${req} due to it being a Python builtin`);
                continue;
            }
            console.log(`[Loader][${item.name}] Python => Installing ${req}`);
            try {
                child_process.spawnSync(`${item.type}`, ["-m", "pip", "install", req], {
                    cwd: `${item.dir}`
                });
            } catch(e) { 
                console.log(`[Loader][${item.name}] Python ERROR => Failed installing requirement... ${err}`);
            }
            console.log(`[Loader][${item.name}] Python => All Requirements installed. Starting...`);
        }
        console.log(`[Loader][${item.name}] Python => Opening file ${item.start_file}`);
        child_process.spawn(`${item.type}`, ["-u", item.start_file], {
            cwd: `${item.dir}`,
            stdio: 'inherit'
        }).on("exit", resolve);
    });
}

for(let i in bots) {
    if(!acceptedTypes.includes(bots[i].type)) {
        console.log(`[Loader][${bots[i].name}] ERROR => TYPE_NOT_SUPPORTED { type: ${bots[i].type } }`);
        continue;
    }
    run(bots[i]);
}