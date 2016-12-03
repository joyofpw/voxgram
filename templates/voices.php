<?php namespace ProcessWire;

include_once './rest/voices/voice.php';
include_once './rest/voices/errors.php';

use \Rest\StatusCode as StatusCode;
use \Rest\Method as Method;
use \Rest\Request as Request;

use \Voices\Errors\VoiceParamsNotFound as VoiceParamsNotFound;
use \Voices\Errors\VoiceCouldNotBeCreated as VoiceCouldNotBeCreated;
use \Voices\Errors\VoiceCouldNotBeCreatedEmojiRepeated as VoiceCouldNotBeCreatedEmojiRepeated;
use \Voices\Errors\VoiceCouldNotBeCreatedLimitExceeded as VoiceCouldNotBeCreatedLimitExceeded;
use \Voices\Errors\VoiceCouldNotBeCreatedFileIdAlreadyExists as VoiceCouldNotBeCreatedFileIdAlreadyExists;

use \Voices\Voice as Voice;

$response->renderErrorAndExitUnlessTheseMethodsAreUsed([Method::POST, Method::GET]);

if (Request::isGet()) {

	$voices = new PageArray();

	$username = $sanitizer->selectorValue(Request::getParam('username'));

	$query = $sanitizer->selectorValue(Request::getParam('query'));

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

			$voices = $pages->find("template=voice, fileTitle|about|tags*=$query, limit=50, sort=-created, havePublicAccess=1");

			$response->meta['query'] = $query;
		}

		if ($voices->count() <= 0) {

			$voices = $pages->find("template=voice, limit=50, sort=random, havePublicAccess=1");

			$response->meta['random'] = true;
		}
	}
	

	$results = [];

	foreach($voices as $voice) {
		
		$object = new Voice($voice);

		$results[] = $object->output;
	}

	$response->data = $results;

	$response->renderAndExit();
}

if (Request::isPost()) {

	// {'id': 'cf180f21-8ba5-4c25-888e-5a0cf4a63a82', 
	// 'description': 'asdaf', 'tags': ['aasdasdf'], 
	// 'file_id': 'AwADAQADtwEAAsRXygMuCtFu2r3QBgI', 
	// 'username': 'clsource', 'title': 'asdf', 'type': 'voice'}

	// required
	$id = trim($sanitizer->text(Request::getParam('id')));

	$file_id = trim($sanitizer->text(Request::getParam('file_id')));

	$username = trim($sanitizer->text(Request::getParam('username')));

	$title = trim($sanitizer->text(Request::getParam('title')));

	$description = trim($sanitizer->text(Request::getParam('description')));

	// optional
	$tags = trim($sanitizer->text(Request::getParam('tags')));

	$public = trim($sanitizer->text(Request::getParam('public', true)));

	if ($public == false || $public == 'False') {
		$public = false;
	} else {
		$public = true;
	}

	// Check Required Params
	$params = [
		'id' => $id,
		'file_id' => $file_id,
		'username' => $username,
		'title' => $title,
		'description' => $description,
	];

	$response->renderErrorAndExitIfTheseParamsAreNotFound($params, 
		VoiceParamsNotFound::error());

	try {
		
		$telegram_user_page_name = $sanitizer->name($username);

		$telegram_user = $pages->get("name=$telegram_user_page_name");

		if ($telegram_user instanceof NullPage) {
			
			$telegram_user = new Page();
			$telegram_user->template = 'telegram-user';
			$telegram_user->parent = '/voices';
			
			$telegram_user->name = $telegram_user_page_name;
			$telegram_user->save();

			$telegram_user->title = $username;

			$telegram_user->save();
		}

		$telegram_user->setOutputFormatting(false);


		if ($telegram_user->numChildren >= MAX_VOICES) {

			$logger("Limit Exceeded");

			$error = VoiceCouldNotBeCreatedLimitExceeded::error();
			
			$response->meta['max_items'] = MAX_VOICES;
			$response->meta['items'] = $telegram_user->numChildren;

			$response->renderErrorAndExit($error);
		}

		if(\Helpers\UTF8::char_in_string($description, $telegram_user->usedEmojis)) {

				$logger("Previous Emoji Found $emoji");

				$response->renderErrorAndExit(VoiceCouldNotBeCreatedEmojiRepeated::error());
		}

		$pageWithTheSameFileId = $telegram_user->children->get("fileId=$file_id");

		if(!($pageWithTheSameFileId == null || $pageWithTheSameFileId instanceof NullPage)) {
			
			$logger("The same file id exists $file_id");

			$conflict_page = new Voice($pageWithTheSameFileId);

			$response->meta['conflict_page'] = $conflict_page->output;
			$response->meta['conflict_file_id'] = $file_id;

			$response->renderErrorAndExit(VoiceCouldNotBeCreatedFileIdAlreadyExists::error());
		}
		

		$name = $sanitizer->name("$title");

		$voice = new Page();
		
		$voice->template = 'voice';
		$voice->parent = $telegram_user;
		
		$voice->name = $name;
		$voice->save();

		$voice->title = $sanitizer->text("$title");
		$voice->fileTitle = $title;
		$voice->username = $username;
		
		$voice->fileId = $file_id;
		$voice->about = $description;
		$voice->tags = $tags;
		$voice->havePublicAccess = $public;

		$voice->save();

		$telegram_user->setOutputFormatting(false);
		$telegram_user->usedEmojis = $telegram_user->usedEmojis . $description;
		$telegram_user->save();

		$response->responseCode = StatusCode::created();

		$object = new Voice($voice);

		$response->data = $object->output;

		$stats = $pages->get('/stats');
		$stats->of(false);
		$stats->totalVoiceFiles += 1;
		$stats->save();

		$logger("New Voice File Created for User $username");

		$response->renderAndExit();

	} catch (\Exception $e) {

		$logger($e->getMessage());

		$response->renderErrorAndExit(VoiceCouldNotBeCreated::error());
	}
}