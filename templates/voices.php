<?php
namespace Processwire;

use Rest\Errors\MethodNotAllowed as MethodNotAllowed;
use Rest\Method as Method;
use Rest\Request as Request;

$params = Request::params();

$response->allowMethods([Method::POST, Method::GET]);

if (!(Request::isPost() || Request::isGet())) {

	$response->setError(MethodNotAllowed::error());
	$response->render();
	exit;
}

if (Request::isGet()) {

	$voices = new PageArray();

	$username = (array_key_exists('username', $params) ? 
		$sanitizer->selectorValue($params['username']) : 
		null); 

	$query = (array_key_exists('query', $params) ? 
		$sanitizer->selectorValue($params['query']) : 
		null); 

	if (isset($username) && $username != '') {
	
		$selector = "template=voice, username=$username, limit=50, sort=-created";

		if(isset($query) && $query != ''){
			$selector .= ", fileTitle|about|tags*=$query";
			$response->output['_meta']['query'] = $query;
		}

		$voices = $pages->find($selector);
	
		$response->output['_meta']['user'] = $username;

	} else {
		

		if (isset($query) && $query != '') {

			$voices = $pages->find("template=voice, fileTitle|about|tags*=$query, limit=50, sort=-created");

			$response->output['_meta']['query'] = $query;
		}

		if ($voices->count() <= 0) {

			$voices = $pages->find("template=voice, limit=50, sort=random");

			$response->output['_meta']['random'] = true;
		}
	}
	

	$results = [];

	foreach($voices as $voice) {
		
		$object['id'] = (int) $voice->id;
		$object['name'] = (string) $voice->name;
		$object['username'] = (string) $voice->username;
		$object['file_id'] = (string) $voice->fileId;
		$object['description'] = (string) $voice->about;
		$object['tags'] = (string) $voice->tags;
		$object['title'] = (string) $voice->fileTitle;
		$object['url'] = (string) $voice->httpUrl;
		$object['created_at'] = (int) $voice->created;

		$results[] = $object;
	}

	$response->output['data'] = $results;
}

$response->render();