"""
ClickUp CLI - Command-line interface for ClickUp document management.
"""

import argparse
import os
import sys
from pathlib import Path

from src.clickup.integration import ClickUpIntegration, get_clickup_client


def cmd_list_spaces(args):
	"""List all spaces."""
	client = get_clickup_client(api_token=args.token, team_id=args.team_id)
	spaces = client.get_spaces()
	
	print(f"\n📁 Found {len(spaces)} spaces:\n")
	for space in spaces:
		print(f"  • {space.get('name', 'Unknown')} (ID: {space.get('id', 'N/A')})")


def cmd_list_folders(args):
	"""List folders in a space."""
	client = get_clickup_client(api_token=args.token)
	folders = client.get_folders(args.space_id)
	
	print(f"\n📂 Found {len(folders)} folders in space:\n")
	for folder in folders:
		print(f"  • {folder.get('name', 'Unknown')} (ID: {folder.get('id', 'N/A')})")


def cmd_list_documents(args):
	"""List documents in a folder."""
	client = get_clickup_client(api_token=args.token)
	documents = client.get_documents(args.folder_id)
	
	print(f"\n📄 Found {len(documents)} documents:\n")
	for doc in documents:
		doc_id = doc.get('id', 'N/A')
		doc_name = doc.get('name', 'Unknown')
		print(f"  • {doc_name} (ID: {doc_id})")


def cmd_get_document(args):
	"""Get a document by ID."""
	client = get_clickup_client(api_token=args.token)
	document = client.get_document(args.document_id)
	
	if document:
		print(f"\n📄 Document: {document.get('name', 'Unknown')}\n")
		print(f"ID: {document.get('id', 'N/A')}")
		print(f"Content Type: {document.get('content_type', 'N/A')}")
		print(f"\nContent:\n{document.get('content', 'No content')}")
	else:
		print("❌ Document not found")


def cmd_create_document(args):
	"""Create a new document."""
	client = get_clickup_client(api_token=args.token)
	
	# Read content from file if provided, otherwise use content arg
	if args.file:
		with open(args.file, 'r', encoding='utf-8') as f:
			content = f.read()
		name = args.name or Path(args.file).stem
	else:
		content = args.content or ""
		name = args.name
	
	if not name:
		print("❌ Document name required (use --name or --file)")
		return
	
	doc = client.create_document(args.folder_id, name, content, args.content_type)
	
	if doc:
		print(f"✅ Document created: {doc.get('name', name)}")
		print(f"   ID: {doc.get('id', 'N/A')}")
	else:
		print("❌ Failed to create document")


def cmd_update_document(args):
	"""Update a document."""
	client = get_clickup_client(api_token=args.token)
	
	# Read content from file if provided, otherwise use content arg
	if args.file:
		with open(args.file, 'r', encoding='utf-8') as f:
			content = f.read()
	else:
		content = args.content
	
	data = {}
	if args.name:
		data['name'] = args.name
	if content:
		data['content'] = content
	
	if not data:
		print("❌ Nothing to update (provide --name or --content/--file)")
		return
	
	doc = client.update_document(args.document_id, **data)
	
	if doc:
		print(f"✅ Document updated: {doc.get('name', 'Unknown')}")
	else:
		print("❌ Failed to update document")


def cmd_upload_document(args):
	"""Upload a local document to ClickUp."""
	client = get_clickup_client(api_token=args.token)
	doc = client.upload_document_from_file(args.folder_id, args.file, args.name)
	
	if doc:
		print(f"✅ Document uploaded: {doc.get('name', 'Unknown')}")
		print(f"   ID: {doc.get('id', 'N/A')}")
	else:
		print("❌ Failed to upload document")


def cmd_sync_document(args):
	"""Sync a local document to ClickUp (create or update)."""
	client = get_clickup_client(api_token=args.token)
	
	# Read local file
	with open(args.file, 'r', encoding='utf-8') as f:
		content = f.read()
	
	name = args.name or Path(args.file).stem
	doc = client.sync_document(args.folder_id, name, content, create_if_missing=True)
	
	if doc:
		print(f"✅ Document synced: {doc.get('name', name)}")
		print(f"   ID: {doc.get('id', 'N/A')}")
	else:
		print("❌ Failed to sync document")


def main():
	parser = argparse.ArgumentParser(description="ClickUp Document Management CLI")
	parser.add_argument("--token", help="ClickUp API token (or set CLICKUP_API_TOKEN)")
	parser.add_argument("--team-id", help="ClickUp Team ID (or set CLICKUP_TEAM_ID)")
	
	subparsers = parser.add_subparsers(dest="command", help="Commands")
	
	# List spaces
	spaces_parser = subparsers.add_parser("spaces", help="List all spaces")
	spaces_parser.set_defaults(func=cmd_list_spaces)
	
	# List folders
	folders_parser = subparsers.add_parser("folders", help="List folders in a space")
	folders_parser.add_argument("space_id", help="Space ID")
	folders_parser.set_defaults(func=cmd_list_folders)
	
	# List documents
	docs_parser = subparsers.add_parser("docs", help="List documents in a folder")
	docs_parser.add_argument("folder_id", help="Folder ID")
	docs_parser.set_defaults(func=cmd_list_documents)
	
	# Get document
	get_parser = subparsers.add_parser("get", help="Get a document by ID")
	get_parser.add_argument("document_id", help="Document ID")
	get_parser.set_defaults(func=cmd_get_document)
	
	# Create document
	create_parser = subparsers.add_parser("create", help="Create a new document")
	create_parser.add_argument("folder_id", help="Folder ID")
	create_parser.add_argument("--name", help="Document name")
	create_parser.add_argument("--content", help="Document content")
	create_parser.add_argument("--file", help="Read content from file")
	create_parser.add_argument("--content-type", default="md", help="Content type (md, txt, docx)")
	create_parser.set_defaults(func=cmd_create_document)
	
	# Update document
	update_parser = subparsers.add_parser("update", help="Update a document")
	update_parser.add_argument("document_id", help="Document ID")
	update_parser.add_argument("--name", help="New document name")
	update_parser.add_argument("--content", help="New document content")
	update_parser.add_argument("--file", help="Read content from file")
	update_parser.set_defaults(func=cmd_update_document)
	
	# Upload document
	upload_parser = subparsers.add_parser("upload", help="Upload a local document")
	upload_parser.add_argument("folder_id", help="Folder ID")
	upload_parser.add_argument("file", help="Local file path")
	upload_parser.add_argument("--name", help="Document name (defaults to filename)")
	upload_parser.set_defaults(func=cmd_upload_document)
	
	# Sync document
	sync_parser = subparsers.add_parser("sync", help="Sync local document to ClickUp")
	sync_parser.add_argument("folder_id", help="Folder ID")
	sync_parser.add_argument("file", help="Local file path")
	sync_parser.add_argument("--name", help="Document name (defaults to filename)")
	sync_parser.set_defaults(func=cmd_sync_document)
	
	args = parser.parse_args()
	
	if not args.command:
		parser.print_help()
		return
	
	if not args.token and not os.getenv("CLICKUP_API_TOKEN"):
		print("❌ ClickUp API token required. Set CLICKUP_API_TOKEN or use --token")
		return
	
	args.func(args)


if __name__ == "__main__":
	main()

