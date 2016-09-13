<?php
namespace Processwire;

include_once './rest/voices/voice.php';
include_once './rest/voices/errors.php';

use Rest\StatusCode as StatusCode;
use Rest\Method as Method;
use Rest\Request as Request;

use Rest\Errors\MethodNotAllowed as MethodNotAllowed;

use Voices\Errors\VoiceParamsNotFound as VoiceParamsNotFound;
use Voices\Errors\VoiceCouldNotBeCreated as VoiceCouldNotBeCreated;

use Voices\Voice as Voice;

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
			$response->meta['query'] = $query;
		}

		$voices = $pages->find($selector);
	
		$response->meta['user'] = $username;

	} else {
		

		if (isset($query) && $query != '') {

			$voices = $pages->find("template=voice, fileTitle|about|tags*=$query, limit=50, sort=-created");

			$response->meta['query'] = $query;
		}

		if ($voices->count() <= 0) {

			$voices = $pages->find("template=voice, limit=50, sort=random");

			$response->meta['random'] = true;
		}
	}
	

	$results = [];

	foreach($voices as $voice) {
		
		$object = new Voice($voice);

		$results[] = $object->output;
	}

	$response->data = $results;
}

if (Request::isPost()) {

	// {'id': 'cf180f21-8ba5-4c25-888e-5a0cf4a63a82', 'description': 'asdaf', 'tags': ['aasdasdf'], 'file_id': 'AwADAQADtwEAAsRXygMuCtFu2r3QBgI', 'username': 'clsource', 'title': 'asdf', 'type': 'voice'}

	// required
	$id = (array_key_exists('id', $params) ? 
		trim($sanitizer->text($params['id'])) : null);

	$file_id = (array_key_exists('file_id', $params) ? 
		trim($sanitizer->text($params['file_id'])) : null);

	$username = (array_key_exists('username', $params) ? 
		trim($sanitizer->text($params['username'])) : null); 

	$title = (array_key_exists('title', $params) ?
		trim($sanitizer->text($params['title'])) : null);

	// optional
	$description = (array_key_exists('description', $params) ?
		trim($sanitizer->text($params['description'])) : '');

	var_dump($params['tags']);
	
	$tags = (array_key_exists('tags', $params) ?
		trim($sanitizer->text($params['tags'])) : '');

	// Check Required Params
	if (!(isset($id) && isset($file_id) && isset($username) && isset($title) &&
		$id != '' && $file_id != '' && $username != '' && $title != '')) {
		
		$response->setError(VoiceParamsNotFound::error());

		$response->meta['required'] = ['id', 'file_id', 'username', 'title'];
		$response->meta['params'] = $params;

	} else {

		try {
			
			$name = $sanitizer->name("$username-$title");

			$voice = new Page();
			
			$voice->template = 'voice';
			$voice->parent = '/voices';
			
			$voice->name = $name;
			$voice->save();

			$voice->title = $sanitizer->text("$username - $title");
			$voice->fileTitle = $title;
			$voice->username = $username;
			
			$voice->fileId = $file_id;
			$voice->about = $description;
			$voice->tags = $tags;
			
			$voice->save();

			$response->responseCode = StatusCode::created();

			$object = new Voice($voice);

			$response->data = $object->output;

		} catch (\Exception $e) {
			$response->setError(VoiceCouldNotBeCreated::error());
			$response->meta['about'] = 'Problem Saving Voice In Database. Probably the user has two voices with the same title.';
		}
	}
}

$response->render();