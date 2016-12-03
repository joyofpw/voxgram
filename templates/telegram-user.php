<?php namespace ProcessWire;

include_once './rest/voices/voice.php';
use \Voices\Voice as Voice;

use \Rest\Method as Method;
use \Rest\Request as Request;

$params = Request::params();

$response->renderErrorAndExitUnlessTheseMethodsAreUsed(Method::GET);


if (Request::isGet()) {

	$voices = $page->children("limit=" . MAX_VOICES);

	$sounds = [];

	foreach($voices as $voice) {
		$object = new Voice($voice);
		$sounds['data'][] = $object->output;
	}

	$sounds['max'] = (int) MAX_VOICES;
	$sounds['quantity'] = (double) $page->numChildren;
	$sounds['available'] = (int) MAX_VOICES - $page->numChildren;

	$data['user'] = [
		"id" => (double) $page->id,
		"name" => (string) $page->name,
		"username" => (string) $page->title,
		"usedEmojis" => (string) $page->usedEmojis,
		"voices" => $sounds,
		"created_at" => (int) $page->created,
		'_href' => [
					'self' => (string) $page->httpUrl,
					'parent' => (string) $page->parent->httpUrl
				]
	];

	$response->data = $data;
	$response->renderAndExit();
}
