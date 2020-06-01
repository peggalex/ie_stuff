var port = 2500; 
var express = require('express');

var app = express();

const neo4j = require('neo4j-driver')
const driver = neo4j.driver("bolt://localhost:7687", neo4j.auth.basic('neo4j', 'neo4j'))

var bodyParser = require('body-parser');
app.use(bodyParser.json()); // support json encoded bodies
app.use(bodyParser.urlencoded({ extended: true })); // support encoded bodies
app.use(express.static('static-files')); 


app.listen(port, function () {
	console.log('Example app listening on port '+port);
  });
  

function arrayRemove(array, element){

	let index = array.indexOf(element);
	if(index!=-1) array.splice(index,1);
}

const io = require('socket.io-client');
const socket = io.connect('http://localhost:5000');

socket.on('connect', function() {
	console.log('connected to flask.');
})
socket.on('disconnect', ()=>{
	throw Error('flask disconnected.')
});

// ================================================================================
// ================================================================================
// ================================================================================

class MyErrors{
	constructor(msg = '', statusCode){
		this.message = `Error: ${msg}`;
		this.statusCode = statusCode;
	}
}

// some user-defined errors
class DatabaseError extends MyErrors{
	constructor(msg){super(msg, 500);}
}
class InputError extends MyErrors{
	constructor(msg){super(msg, 400);}
}
class NotFoundError extends MyErrors{
	constructor(msg){super(msg, 404);}
}
class BadAuthError extends MyErrors{
	constructor(msg){super(msg, 401);}
}
class ForbiddenError extends MyErrors{
	constructor(msg){super(msg, 403);}
}
class ConflictError extends MyErrors{
	constructor(msg){super(msg, 409);}
}
class BadWebSocketError extends MyErrors{
	constructor(msg){super(msg, null);}
}

/* throws DatabaseError, NotFoundError */
async function querySingle(queryString, kwargs = {}){
	return new Promise(async (resolve, reject) => {
		let session = driver.session(),
			result;
		try {
			result = await session.run(
				`${queryString} LIMIT ${RETURN_LIMIT}`,
				kwargs
			);
		} catch (e) {
			await session.close();
			reject(new DatabaseError(e.message))
		}
		await session.close();

		if (result.records.length == 0){
			reject(new NotFoundError(`${queryString} < ${kwargs} not found.`))
		}
		resolve(result.records[0]._fields[0]);
	});
}

const RETURN_LIMIT = 5;

/* throws DatabaseError */
async function query(queryString, kwargs = {}){
	return new Promise(async (resolve, reject) => {
		let session = driver.session(),
			result;
		try {
			result = await session.run(
				`${queryString} LIMIT ${RETURN_LIMIT};`,
				kwargs
			);
		} catch (e) {
			await session.close();
			reject(new DatabaseError(e.message))
		}
		await session.close();
		resolve(result.records.map((record) => record.get(0).properties));
	});
}

async function handleResponseErrors(e, res){
	if (e instanceof MyErrors){
		res.status(e.statusCode);
	} else {
		res.status(500);
	}
	res.send({error: e.message});
	console.log(e.message);
}

// input sanitisation
isAlphaNumeric = (str) => RegExp("^[0-9a-zA-Z]+$").test(str);
isHex = (str) => RegExp("^[0-9a-fA-F]+$").test(str);
isUrl = (str) => RegExp(/^[^ <>\{\}\\(\\);]+$/g).test(str); //https://www.urlencoder.io/learn/


// ================================================================================
// ================================================================================
// ================================================================================

app.use('/',express.static('static_files')); // this directory has files to be returned


function validateInput(filter, url){
	if (!['vulgarity', 'malware', 'pornography'].some((s)=>filter==s)){
		throw new InputError('invalid filter type');
	}
	if (!isUrl(url)){
		throw new InputError('invalid symbols');
	}
}

app.get('/filterQuery/:f/url/:u', async function(req,res){
	
	let filter = req.params.f,
		url = req.params.u;

	try {
		validateInput(filter, url);

		let result = await query(`
				MATCH (r:Record)
				WHERE r.url CONTAINS $url
				RETURN r
				ORDER BY r.url
			`,
			{url: url}
		);
		let ret = await Promise.all(result.map(async (obj)=>{
			return {
				url: obj.url,
				pred: await filters[filter].isFlagged(obj.url),
				risk: obj.risk
			}
		}));

		res.status(200);
		res.send({
			urls: ret,
			url: url,
			pred: await filters[filter].isFlagged(url),
		});
	} catch (e) {
		handleResponseErrors(e, res);
	}
});

class Filter{
	static async isFlagged(url){
		throw Error('unimplemented abstract method');
	}
}
const swears = ["anal", "anus", "arse", "ballsack", "balls", "bastard", "bitch", "biatch", "bloody", "blowjob", "blow job", "bollock", "bollok", "boner", "boob", "bugger", "bum", "butt", "buttplug", "clitoris", "cock", "coon", "crap", "cunt", "damn", "dick", "dildo", "dyke", "fag", "feck", "fellate", "fellatio", "felching", "fuck", "fudgepacker", "flange", "Goddamn", "God damn", "hell", "homo", "jerk", "jizz", "knobend", "labia", "lmao", "lmfao", "muff", "nigger", "nigga", "omg", "penis", "piss", "poop", "prick", "pube", "pussy", "queer", "scrotum", "sex", "shit", "sh1t", "slut", "smegma", "spunk", "tit", "tosser", "turd", "twat", "vagina", "wank", "whore", "wtf", "urbandictionary"]; 

class VulgarityFilter extends Filter {
	//@override
	static async isFlagged(url){
		return swears.some((swear)=>url.includes(swear));
	}
}

class MalwareFilter extends Filter {
	//@override
	static async isFlagged(url){
		return Boolean(await querySingle(`
				MATCH (a:Ad)
				WITH collect(a.regex) as regexs
				RETURN any(regex IN regexs WHERE $url =~ regex) AS isFlagged
			`, {url: url}
		));
	}
}

class PornFilter extends Filter {
	//@override
	static async isFlagged(url){
		socket.emit('reqIsPorn', {url: url});
		return new Promise((resolve, reject)=>{
			socket.once('resIsPorn', (json)=>{
				if (json.error) { resolve(null) }
				resolve(json.pred);
			})
		});

	}
}

filters = {
	'vulgarity': VulgarityFilter,
	'malware': MalwareFilter,
	'pornography': PornFilter
}